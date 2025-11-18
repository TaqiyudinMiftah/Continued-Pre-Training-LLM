# crawl_and_make_cpt_txt_strip_prefix.py
import asyncio
import os
import time
import base64
import random
import re
from typing import Dict
from urllib.parse import urlparse, parse_qs, unquote
from difflib import SequenceMatcher

from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# ---------- CONFIG ----------
INPUT_CSV = os.getenv("INPUT_CSV_LINK", "data/url/link.csv")
OUTPUT_TXT = os.getenv("OUTPUT_TXT_RESULT", "data/results/cpt_ready.txt")
MAX_CONCURRENCY = 15
NAV_TIMEOUT = 10000
PAGE_WAIT_AFTER = 0.8
MAX_CHARS_PER_LINE = None   # None = tidak dibatasi
# ----------------------------

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ",
    "AppleWebKit/537.36 (KHTML, like Gecko) ",
    "Chrome/131.0.6770.85 Safari/537.36 Brave/1.68.120",

    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ",
    "AppleWebKit/537.36 (KHTML, like Gecko) ",
    "Chrome/130.0.6700.62 Safari/537.36 Brave/1.67.98",
    
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ",
    "AppleWebKit/537.36 (KHTML, like Gecko) ",
    "Chrome/131.0.0.0 Safari/537.36 ",
    "(Not:A-Brand; Brand:Chromium; Version:131.0.0.0)",

    "Mozilla/5.0 (X11; Linux x86_64) ",
    "AppleWebKit/537.36 (KHTML, like Gecko) ",
    "Chrome/129.0.0.0 Safari/537.36 ",
    "(Not:A-Brand; Brand:Google Chrome; Version:129.0.0.0)"
]

# minimal domain extractors (pakai extractor Anda)
DOMAIN_EXTRACTORS = {
    "detik.com": """
        (() => {
          return Array.from(document.querySelectorAll("div.detail__body-text p"))
            .filter(p => !p.classList.contains("para_caption"))
            .map(p => p.innerText.trim()).join("\\n\\n");
        })();
    """,
    "teknologi.id": """
        (() => {
          return Array.from(
            document.querySelectorAll("div.text-content p")
          )
            .filter(p => 
              !p.querySelector("img") && 
              !p.innerText.trim().startsWith("Foto :") &&
              !p.innerText.trim().startsWith("Baca Juga:") &&
              !p.innerText.trim().startsWith("Baca berita dan artikel lainnya di Google News")
            )
            .map(el => el.innerText.trim())
            .filter(text => text.length > 0)
            .join("\\n\\n");
        })();
    """,
    "ibm.com": """
        (() => {
          return Array.from(
            document.querySelectorAll(
              "div.cms-richtext p, \
               div.cms-richtext ol, \
               div.cms-richtext ul, \
               div.cms-richtext li, \
               div.cms-richtext blockquote"
            )
          )
            .filter(el => 
              !el.closest(".author-signature")
            )
            .map(el => el.innerText.trim())
            .filter(text => text.length > 0)
            .join("\\n\\n");
        })();
    """,
    "kemnaker.go.id": """
        (() => {
          /* CATATAN: Selector diperbaiki.
            Kita mencari <p> atau <div> yang muncul SETELAH p.news-description
            (menggunakan ~ sibling combinator), BUKAN yang ada di DALAMNYA.
          */
          return Array.from(
            document.querySelectorAll(
              "p.news-description ~ p, \
               p.news-description ~ div"
            )
          )
            .map(el => el.innerText.trim())
            .filter(text => text.length > 0) // Hapus elemen kosong
            .join("\\n\\n");
        })();
    """,
    "multipolar.com": """
        (() => {
          return Array.from(
            document.querySelectorAll("div.entry-content.single-page p")
          )
            .filter(p => 
              !p.closest("div.banner")
            )
            .map(el => el.innerText.trim())
            .filter(text => text.length > 0)
            .join("\\n\\n");
        })();
    """,
    "telkomuniversity.ac.id": """
        (() => {
          return Array.from(
            document.querySelectorAll("div.entry-content p,div.entry-content ol,div.entry-content li, div.entry-content ul,div.entry-content blockquote")
          )
            .map(el => el.innerText.trim())
            .filter(text => text.length > 0) 
            .join("\\n\\n");
        })();
    """,

    "idtechinsider.com": """
        (() => {
          return Array.from(
            document.querySelectorAll("div.tdb-block-inner.td-fix-index p,div.tdb-block-inner.td-fix-index ol,div.tdb-block-inner.td-fix-index li, div.tdb-block-inner.td-fix-index ul,div.tdb-block-inner.td-fix-index blockquote")
          )
            .filter(el => !el.closest("div.comments"))
            .map(el => el.innerText.trim())
            .filter(text => text.length > 0) 
            .join("\\n\\n");
        })();
    """,
    "dealls.com": """
        (() => {
          return Array.from(
            document.querySelectorAll(
              "article#article-content p, \\
               article#article-content ol, \\
               article#article-content ul, \\
               article#article-content li, \\
               article#article-content blockquote"
            )
          )
            .filter(el => !el.querySelector("a"))
            .filter(p => 
              !p.innerText.trim().startsWith("Ayo, capai karir impianmu bersama Dealls!") &&
              !p.innerText.trim().startsWith("Sumber:")
            )
            .map(el => el.innerText.trim())
            .filter(text => text.length > 0) 
            .join("\\n\\n");
        })();
    """,
    "tirto.id": """
        (() => {
          return Array.from(
            document.querySelectorAll(
              "div.content-text-editor p, \
               div.content-text-editor ol, \
               div.content-text-editor ul, \
               div.content-text-editor li, \
               div.content-text-editor blockquote"
            )
          )
            .map(el => el.innerText.trim())
            .filter(text => text.length > 0)
            .join("\\n\\n");
        })();
    """,
    "msn.com": """
        (() => {
          const shadowRoot = document.querySelector("cp-article")?.shadowRoot;
          if (!shadowRoot) {
            return ""; // Kembalikan string kosong jika shadow root tidak ada
          }
          
          return Array.from(
            // PERBAIKAN: Selector ini menargetkan <p> di dalam body 
            // yang memiliki atribut data-t 'bluelinks'
            shadowRoot.querySelectorAll("body.article-body p[data-t*='bluelinks']")
          )
            .filter(p =>
              // Hapus paragraf "baca juga"
              !p.classList.contains("bacajuga-inside")
            )
            .map(el => el.innerText.trim())
            .filter(text => text.length > 0) // Hapus paragraf kosong
            .join("\\n\\n");
        })();
    """,
    "telkom.co.id": """
        (() => {
          /* CATATAN: Kode Anda menggunakan 'article-pharagraph'.
             Jika tidak ada hasil, periksa apakah seharusnya 'article-paragraph'. */
          return Array.from(
            document.querySelectorAll("div.article-pharagraph.flex-grow-1 p")
          )
            .filter(p => 
              !p.querySelector("img") 
            )
            .map(el => el.innerText.trim())
            .filter(text => text.length > 0)
            .join("\\n\\n");
        })();
    """,
    "kompas.com": """
        (() => {
          return Array.from(document.querySelectorAll("div.read__content p"))
          // Modifikasi filter:
          .filter(p => 
            !p.classList.contains("para_caption") && 
            !p.querySelector("a.inner-link-baca-juga")
          )
          .map(p => p.innerText.trim())
          .filter(text => text.length > 0);
        })();
    """,
    "liputan6.com": """
        (() => {
          return Array.from(document.querySelectorAll("div.article-content-body__item-content p, div.article-content-body__item-content ol li"))
            .filter(p => !p.classList.contains("para_caption"))
            .map(p => p.innerText.trim()).join("\\n\\n");
        })();
    """,
    "tempo.co": """
        (() => {
          return Array.from(document.querySelectorAll("#content-wrapper p, #content-wrapper ol, #content-wrapper li"))
            .filter(p => !p.classList.contains("para_caption"))
            .map(p => p.innerText.trim()).join("\\n\\n");
        })();
    """,
    "tribunnews.com": """
        (() => {
          return Array.from(document.querySelectorAll("#article_con .side-article.txt-article.multi-fontsize p, #article_con .side-article.txt-article.multi-fontsize ol, #article_con .side-article.txt-article.multi-fontsize ul, #article_con .side-article.txt-article.multi-fontsize li, #article_con .side-article.txt-article.multi-fontsize blockquote"))
            .filter(p => !p.classList.contains("para_caption"))
            .map(p => p.innerText.trim()).join("\\n\\n");
        })();
    """,
    "cnnindonesia.com": """
        (() => {
          return Array.from(document.querySelectorAll(".detail-wrap .detail-text.text-cnn_black.text-sm.grow.min-w-0 p, .detail-wrap .detail-text.text-cnn_black.text-sm.grow.min-w-0 ol, .detail-wrap .detail-text.text-cnn_black.text-sm.grow.min-w-0 ul, .detail-wrap .detail-text.text-cnn_black.text-sm.grow.min-w-0 li, .detail-wrap .detail-text.text-cnn_black.text-sm.grow.min-w-0 blockquote"))
            .map(p => p.innerText.trim()).filter(t => t.length>0).join("\\n\\n");
        })();
    """,
    "cnbcindonesia.com": """
        (() => {
          return Array.from(document.querySelectorAll(".flex.gap-4 .detail-text.min-w-0 .detail-text p, .flex.gap-4 .detail-text.min-w-0 .detail-text ol, .flex.gap-4 .detail-text.min-w-0 .detail-text li, .flex.gap-4 .detail-text.min-w-0 .detail-text ul, .flex.gap-4 .detail-text.min-w-0 .detail-text blockquote"))
            .filter(p => !p.classList.contains("para_caption"))
            .map(p => p.innerText.trim()).join("\\n\\n");
        })();
    """,
    "antaranews.com": """
        (() => {
          return Array.from(document.querySelectorAll(".wrap__article-detail .wrap__article-detail-content.post-content p, .wrap__article-detail .wrap__article-detail-content.post-content ol, .wrap__article-detail .wrap__article-detail-content.post-content li, .wrap__article-detail .wrap__article-detail-content.post-content ul, .wrap__article-detail .wrap__article-detail-content.post-content blockquote"))
            .filter(p => !p.classList.contains("para_caption"))
            .map(p => p.innerText.trim()).join("\\n\\n");
        })();
    """,
    "kompasiana.com": """
        (() => {
          return Array.from(document.querySelectorAll("div.read-content p, div.read-content ol, div.read-content li, div.read-content ul, div.read-content blockquote"))
            .filter(p => !p.classList.contains("para_caption"))
            .map(p => p.innerText.trim()).join("\\n\\n");
        })();
    """,
    "bbc.com": """
        (() => {
          return Array.from(document.querySelectorAll("main[role='main'] p, main[role='main'] ol, main[role='main'] li, main[role='main'] ul, main[role='main'] blockquote"))
            .filter(el => !el.innerHTML.includes("whatsapp.com"))
            .filter(el => !el.innerText.toLowerCase().includes("whatsapp"))
            .filter(el => !el.closest(".podcastIconWrapper"))
            .filter(el => !el.closest(".css-15oiryy.e1rfboeq4"))
            .filter(el => !el.closest("section[aria-label='Berita terkait']"))
            .filter(el => !el.closest("section[data-e2e='scrollable-promos']"))
            .filter(el => !el.querySelector(".css-m04vo2"))
            .filter(el => !/sumber gambar/i.test(el.innerText))
            .map(el => el.innerText.trim())
            .filter(text => text.length > 0)
            .join("\\n\\n");
        })();
    """,
    "idntimes.com": """
        (() => {
          return Array.from(document.querySelectorAll("p.article-text"))
            .filter(el => !el.closest(".wrapper-ads"))
            .map(el => el.innerText.trim())
            .filter(text => text.length > 0)
            .join("\\n\\n");
        })();
    """,
    "retizen.republika.co.id": """
        (() => {
          return Array.from(
            document.querySelectorAll(".top-selection.news-content p, .top-selection.news-content ol, .top-selection.news-content ul, .top-selection.news-content li, .top-selection.news-content blockquote")
          )
            .map(p => p.innerText.trim())
            .filter(t => t.length > 0)
            .join("\\n\\n");
        })();
    """,
    "republika.co.id": """
        (() => {
          return Array.from(document.querySelectorAll("div.article-content article p, div.article-content article ol, div.article-content article ul, div.article-content article li, div.article-content article blockquote"))
            .filter(el => !el.closest(".picked-article"))
            .map(el => el.innerText.trim())
            .filter(text => text.length > 0)
            .join("\\n\\n");
        })();
    """,
}

# ---------------- helper functions ----------------
def clean_text(text: str) -> str:
    """Bersihkan teks hasil extractor."""
    if not text:
        return ""
    text = re.sub(r'http\S+|www\.\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    # normalisasi whitespace internal (tetap simpan paragraf sebagai newline)
    text = re.sub(r'\r', '\n', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)   # trim multi-blank paragraf
    # kita akan filter paragraf pendek saja
    lines = [ln.strip() for ln in text.splitlines() if len(ln.strip()) > 20]
    return "\n\n".join(lines).strip()

def strip_leading_prefix(text: str) -> str:
    if not text:
        return text
    s = text.lstrip()

    # dash chars: ASCII hyphen + en-dash + em-dash + figure/other dashes
    # do NOT include square brackets here
    dash_chars = r"\-\u2013\u2014\u2012\u2015"

    # pattern: capture up to the dash (limit to 200 chars)
    pattern = re.compile(rf'^(?P<prefix>.{{0,200}}?)[{dash_chars}]\s+', flags=re.UNICODE)

    while True:
        m = pattern.match(s)
        if not m:
            break
        pref = m.group('prefix').strip()

        is_source_like = False
        lower_pref = pref.lower()
        if any(ext in lower_pref for ext in (".com", ".id", ".co", ".net", ".org", ".co.id")):
            is_source_like = True
        elif "," in pref:
            is_source_like = True
        else:
            letters = [c for c in pref if c.isalpha()]
            if letters:
                upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
                if upper_ratio > 0.45 and len(pref) <= 120:
                    is_source_like = True

        if not is_source_like:
            break

        s = s[m.end():].lstrip()

    # final cleanup: remove any leading dash-like char
    s = re.sub(rf'^[{dash_chars}]\s*', '', s)

    return s

def normalize_to_single_line(text: str) -> str:
    """Gabungkan jadi satu baris, hilangkan newline internal, normalize spasi."""
    if not text:
        return ""
    s = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")
    s = re.sub(r"\s+", " ", s).strip()
    if MAX_CHARS_PER_LINE:
        return s[:MAX_CHARS_PER_LINE]
    return s

def decode_bing_ck_target(raw_link: str) -> str:
    """Ambil parameter u= dari link Bing ck/a dan coba decode."""
    try:
        qs = parse_qs(urlparse(raw_link).query)
    except Exception:
        qs = {}
    uval = ""
    if "u" in qs and qs["u"]:
        uval = qs["u"][0]
    elif "ru" in qs and qs["ru"]:
        uval = qs["ru"][0]
    else:
        idx = raw_link.find("&u=")
        if idx != -1:
            v = raw_link[idx+3:]
            amp = v.find("&")
            if amp != -1:
                v = v[:amp]
            uval = v
    if not uval:
        return ""
    try:
        u_dec = unquote(uval)
    except Exception:
        u_dec = uval
    if u_dec.startswith("http"):
        return u_dec
    def try_b64(s):
        try:
            missing = len(s) % 4
            s2 = s + ("=" * (4-missing)) if missing else s
            b = base64.b64decode(s2, validate=False)
            txt = b.decode("utf-8", errors="replace")
            if "http" in txt:
                idx = txt.find("http")
                return txt[idx:]
            return ""
        except Exception:
            return ""
    b = try_b64(u_dec)
    if b:
        return unquote(b)
    pos = u_dec.find("aHR0")
    if pos != -1:
        candidate = u_dec[pos-4:] if pos >= 4 else u_dec[pos:]
        b2 = try_b64(candidate)
        if b2:
            return unquote(b2)
    return u_dec

def find_matching_domain(netloc: str):
    net = netloc.lower()
    for k in DOMAIN_EXTRACTORS.keys():
        key = k.lstrip(".")
        if key in net:
            return key
    return None


# ---------------- worker (parallel) ----------------
async def scrape_worker(item: Dict, browser, sem: asyncio.Semaphore):
    idx = item["idx"]
    raw = item["input_link"]
    out = {"id": idx, "input_link": raw, "target_url": "", "domain": "", "raw_text": "", "clean_text": "", "status": "skipped", "error": ""}

    target = decode_bing_ck_target(raw)
    if not target:
        out["status"] = "no_target"
        return out
    out["target_url"] = target

    parsed = urlparse(target)
    domain = find_matching_domain(parsed.netloc)
    if not domain:
        out["status"] = "domain_not_allowed"
        out["domain"] = parsed.netloc
        return out
    out["domain"] = domain

    async with sem:
        ua = random.choice(UA_POOL)
        context = await browser.new_context(user_agent=ua, locale="id-ID", ignore_https_errors=True)
        page = await context.new_page()
        await context.set_extra_http_headers({"Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7", "Referer": "https://www.bing.com/"})
        try:
            try:
                await page.goto(target, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)
            except PWTimeout:
                try:
                    await page.goto(target, wait_until="networkidle", timeout=NAV_TIMEOUT*2)
                except Exception as e:
                    raise e
            except Exception:
                try:
                    await page.goto(target, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)
                except Exception:
                    raise

            await page.wait_for_timeout(int(PAGE_WAIT_AFTER * 1000))

            extractor_js = DOMAIN_EXTRACTORS.get(domain)
            article_text = ""
            if extractor_js:
                try:
                    article_text = await page.evaluate(extractor_js)
                    if isinstance(article_text, list):
                        article_text = "\n\n".join([str(x).strip() for x in article_text if str(x).strip()])
                except Exception:
                    try:
                        paras = await page.eval_on_selector_all("p", "els=>els.map(e=>e.innerText.trim()).filter(t=>t.length>0).join('\\n\\n')")
                        article_text = paras
                    except Exception:
                        article_text = ""
            else:
                try:
                    paras = await page.eval_on_selector_all("p", "els=>els.map(e=>e.innerText.trim()).filter(t=>t.length>0).join('\\n\\n')")
                    article_text = paras
                except Exception:
                    article_text = ""

            if article_text and isinstance(article_text, str):
                out["raw_text"] = article_text.strip()
                cleaned = clean_text(out["raw_text"])
                # strip leading prefix only (awalan) then normalize to single-line
                cleaned = strip_leading_prefix(cleaned)
                out["clean_text"] = normalize_to_single_line(cleaned)
                out["status"] = "ok" if out["clean_text"] else "no_text"
            else:
                out["status"] = "no_text"
        except Exception as e:
            out["error"] = str(e)
            out["status"] = "error"
        finally:
            try:
                await context.close()
            except Exception:
                pass
            await asyncio.sleep(0.25 + random.random() * 0.5)
    return out

# ---------------- orchestrator ----------------
async def main():
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(INPUT_CSV)
    raw_links = []
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        for line in f:
            v = line.strip()
            if not v or v.lower() in ("result_link","url"):
                continue
            raw_links.append(v)

    # ------------------ dedupe by string-equality (keep order) ------------------
    seen = set(); unique_links = []
    for u in raw_links:
        if u not in seen:
            unique_links.append(u); seen.add(u)

    # build inputs preserving order from deduped_links
    inputs = []
    for i, u in enumerate(unique_links, start=1):
        inputs.append({"idx": i, "input_link": u})

    os.makedirs(os.path.dirname(OUTPUT_TXT), exist_ok=True)
    
    total_links = len(inputs)
    written = 0
    
    sem = asyncio.Semaphore(MAX_CONCURRENCY)
    
    print(f"--- Processing {total_links} URLs (Concurrency={MAX_CONCURRENCY}) ---")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        
        # Buat daftar tasks
        tasks = [scrape_worker(item, browser, sem) for item in inputs]

        # Buka file output
        with open(OUTPUT_TXT, "w", encoding="utf-8", newline="") as fout:
            
            # Gunakan asyncio.as_completed untuk mendapatkan hasil SATU PER SATU
            # saat mereka selesai, sambil tetap berjalan paralel
            for future in asyncio.as_completed(tasks):
                
                # 'await future' akan menunggu TUGAS BERIKUTNYA yang selesai
                r = await future
                
                # === LOGIKA PRINT DAN TULIS PINDAH KE SINI ===
                idx = r.get("id", 0)
                status = r.get("status", "unknown")
                domain = r.get("domain", "")
                target_url = r.get("target_url") if r.get("target_url") else r.get("input_link", "")

                if status == "ok":
                    # [419/461] NAV -> ... (domain=kompasiana.com)
                    print(f"[{idx}/{total_links}] NAV -> {target_url} (domain={domain})")
                    
                    clean_txt = r.get("clean_text","") or ""
                    if clean_txt:
                        # Tulis ke file segera
                        fout.write(clean_txt + "\n\n")
                        written += 1
                    else:
                        # Jika teks bersihnya kosong
                        print(f"[{idx}/{total_links}] SKIP: text was empty after clean -> {target_url}")

                elif status == "domain_not_allowed":
                    # [420/461] SKIP: domain not in allowed list -> jurnal.dpr.go.id
                    print(f"[{idx}/{total_links}] SKIP: domain not in allowed list -> {domain if domain else target_url}")
                
                elif status == "no_text":
                    print(f"[{idx}/{total_links}] SKIP: no text found -> {target_url}")
                
                elif status == "no_target":
                    print(f"[{idx}/{total_links}] SKIP: no target URL -> {target_url}")
                    
                elif status == "error":
                    print(f"[{idx}/{total_links}] ERROR: {r.get('error', 'Unknown error')} -> {target_url}")

                else:
                    # Menangkap status lain
                    print(f"[{idx}/{total_links}] SKIP: {status} -> {target_url}")
                # === AKHIR DARI LOGIKA ===

    # Browser akan ditutup secara otomatis di sini oleh 'async with pw'

    print("DONE. CPT TXT:", OUTPUT_TXT, "(articles written:", written, ")")

if __name__ == "__main__":
    asyncio.run(main())
