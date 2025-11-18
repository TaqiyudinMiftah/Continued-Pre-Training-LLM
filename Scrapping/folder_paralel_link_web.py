import asyncio, csv, os, re, random, uuid
from pathlib import Path
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from playwright.async_api import async_playwright

# ----------------- PENGATURAN PARALLEL & TIMEOUT -----------------
MAX_CONCURRENCY = 15
NAV_TIMEOUT = 30000       # ms
PAGE_WAIT_AFTER = 1     # detik
# ---------------------------------------------------------------

INPUT_DIR = os.getenv("INPUT_DIR_PAGE", "data/page")
OUTPUT_CSV = os.getenv("OUTPUT_CSV_LINK", "data/url/link.csv")

# UA pool besar
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


# ------------------ STEALTH INIT SCRIPT ------------------
STEALTH_JS = r"""
// webdriver flag
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

// languages
Object.defineProperty(navigator, 'languages', { get: () => ['id-ID','id'] });

// plugins
Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4] });

// mimeTypes
Object.defineProperty(navigator, 'mimeTypes', { get: () => [1,2] });

// chrome runtime
window.chrome = { runtime: {} };

// notifications
if (typeof Notification !== 'undefined') {
  Object.defineProperty(Notification, 'permission', { get: () => 'denied' });
}
"""
# -----------------------------------------------------------


def read_urls_from_csv(path: str):
    if not Path(path).exists():
        raise FileNotFoundError(path)
    urls = []
    with open(path, "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row:
                continue
            u = row[0].strip()
            if not u or u.lower() == "url":
                continue
            urls.append(u)
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            out.append(u); seen.add(u)
    return out


def canonicalize_bing_url(u: str) -> str:
    p = urlparse(u)
    qd = dict(parse_qsl(p.query, keep_blank_values=True))

    keep = {}
    if "q" in qd: keep["q"] = qd["q"]
    if "first" in qd: keep["first"] = qd["first"]
    if "FORM" in qd: keep["FORM"] = qd["FORM"]

    keep["setLang"] = "id"
    keep["mkt"]     = "id-ID"
    keep["cc"]      = "ID"
    keep["cvid"]    = uuid.uuid4().hex
    keep["_ts"]     = uuid.uuid4().hex

    new_q = urlencode(keep, doseq=True)
    return urlunparse((p.scheme, p.netloc, p.path, p.params, new_q, p.fragment))


def first_param(u: str) -> int:
    m = re.search(r"[?&]first=(\d+)", u)
    return int(m.group(1)) if m else -1


async def extract_result_links(page):
    await page.wait_for_load_state("domcontentloaded")
    try:
        await page.wait_for_selector("#b_results", timeout=12000)
    except:
        pass

    links = await page.eval_on_selector_all(
        "h2 a[href]",
        "els => els.map(a => a.getAttribute('href'))"
    )
    seen, out = set(), []
    for h in links:
        if h and h not in seen:
            out.append(h); seen.add(h)
    return out



# ------------------ PERUBAHAN UTAMA ADA DI SINI ------------------
async def open_urls_and_extract(urls):
    """
    Versi paralel + stealth + anti bot detection.
    """
    result_links = []
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    async with async_playwright() as pw:

        # Headless = False → lebih aman dari bot detection
        browser = await pw.chromium.launch(headless=True)

        async def worker(idx, raw_url):
            ua = random.choice(UA_POOL)
            async with sem:

                # ---- STEALTH CONTEXT ----
                context = await browser.new_context(
                    user_agent=ua,
                    locale="id-ID",
                )
                await context.add_init_script(STEALTH_JS)

                context.set_default_timeout(NAV_TIMEOUT)
                page = await context.new_page()

                # realistic headers
                await context.set_extra_http_headers({
                    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                    "sec-ch-ua": '"Chromium";v="125", "Google Chrome";v="125", ";Not A Brand";v="99"',
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-ch-ua-mobile": "?0",
                    "Referer": "https://www.bing.com/"
                })

                final_url = canonicalize_bing_url(raw_url) + "&nonce=" + uuid.uuid4().hex

                try:
                    # bersihkan JS caches sebelum masuk
                    try:
                        await page.evaluate("""() => {
                            try { caches.keys().then(k=>k.forEach(c=>caches.delete(c))); } catch(e) {}
                            try { localStorage.clear(); sessionStorage.clear(); } catch(e){}
                        }""")
                    except:
                        pass

                    await page.goto(final_url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)

                    await page.wait_for_timeout(random.randint(300, 900))

                    # sedikit scroll → menghindari bot detection
                    for _ in range(random.randint(1, 3)):
                        await page.mouse.wheel(0, random.randint(100, 350))
                        await page.wait_for_timeout(random.randint(150, 350))

                    links = await extract_result_links(page)

                    print(f"[{idx}/{len(urls)}] first={first_param(final_url)} -> {len(links)} result_link")
                    return links

                except Exception as e:
                    print(f"[{idx}/{len(urls)}] gagal: {e}")
                    return []

                finally:
                    try:
                        await context.close()
                    except:
                        pass

        tasks = [worker(i+1, u) for i, u in enumerate(urls)]
        all_results = await asyncio.gather(*tasks)

        for sub in all_results:
            if isinstance(sub, list):
                result_links.extend(sub)

        await browser.close()

    # dedup
    seen, uniq = set(), []
    for l in result_links:
        if l not in seen:
            uniq.append(l); seen.add(l)
    return uniq
# ------------------------------------------------------------------


def save_results(result_links):
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["result_link"])
        for link in result_links:
            w.writerow([link])
    print(f"OK: {OUTPUT_CSV}")


if __name__ == "__main__":
    p = Path(INPUT_DIR)
    if not p.exists():
        raise FileNotFoundError(f"{INPUT_DIR} tidak ditemukan")

    csv_files = sorted([str(x) for x in p.glob("*.csv")])

    all_result_links = []

    for fp in csv_files:
        print("Processing CSV:", fp)
        try:
            urls = read_urls_from_csv(fp)
            if not urls:
                print("  tidak ada url, skip.")
                continue

            result_links = asyncio.run(open_urls_and_extract(urls))
            for l in result_links:
                all_result_links.append(l)

        except Exception as e:
            print("ERROR processing", fp, e)

    seen, final = set(), []
    for l in all_result_links:
        if l not in seen:
            final.append(l); seen.add(l)

    save_results(final)
