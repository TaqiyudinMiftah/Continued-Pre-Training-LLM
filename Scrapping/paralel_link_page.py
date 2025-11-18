import asyncio
import os
import re
import random
from urllib.parse import quote_plus, urlparse, parse_qsl, urlencode, urlunparse
from playwright.async_api import async_playwright

# ----------------- KONFIGURASI PARALLEL & TIMEOUT -----------------
MAX_CONCURRENCY = 10
NAV_TIMEOUT = 30000        # ms
PAGE_WAIT_AFTER = 0.8      # detik
# -----------------------------------------------------------------

# ============================================================
# 🎭 Pool User-Agent untuk rotasi acak
# ============================================================
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

# ============================================================
# 🔍 Fungsi utama scraping Bing pagination
# ============================================================
async def get_bing_page_links(keyword: str, headless: bool = True):
    base = "https://www.bing.com/search"
    q = keyword.strip()
    url = f"{base}?q={quote_plus(q)}&first=1&mkt=id-ID&cc=ID"
    print(f"\n🔗 Base URL: {url}")

    # --------------------------------------------------------
    # 🔧 Fungsi helper untuk membangun link next-page otomatis
    # --------------------------------------------------------
    def build_next_links(last_url: str, max_first: int = 291, max_pere: int = 28) -> list[str]:
        """Bangun daftar URL baru dengan first naik 10 dan FORM naik 1 (hingga batas)."""
        u = urlparse(last_url)
        qd = dict(parse_qsl(u.query, keep_blank_values=True))

        try:
            cur_first = int(qd.get("first", "1"))
        except ValueError:
            cur_first = 1

        form = qd.get("FORM", "PERE1")
        m = re.fullmatch(r"PERE(\d+)", form)
        cur_pere = int(m.group(1)) if m else 1

        urls = []
        while cur_first < max_first and cur_pere < max_pere:
            cur_first += 10
            cur_pere += 1
            qd["first"] = str(cur_first)
            qd["FORM"] = f"PERE{cur_pere}"
            new_q = urlencode(qd, doseq=True)
            new_url = urlunparse((u.scheme, u.netloc, u.path, u.params, new_q, u.fragment))
            urls.append(new_url)
        return urls

    # ============================================================
    # 🚀 Mulai Playwright + rotasi UA
    # ============================================================
    user_agent = random.choice(UA_POOL)
    print(f"🧩 Menggunakan User-Agent: {user_agent}")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)

        context = await browser.new_context(
            user_agent=user_agent,
            locale="id-ID",
            extra_http_headers={
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "max-age=0",
                "Upgrade-Insecure-Requests": "1",
            },
        )
        page = await context.new_page()

        # 🌐 Buka halaman awal Bing (pakai NAV_TIMEOUT)
        await page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)

        # Klik consent jika muncul
        try:
            btn = await page.query_selector("#bnp_btn_accept, .bnp_btn_accept")
            if btn:
                await btn.click()
                await page.wait_for_timeout(800)
        except Exception:
            pass

        # tunggu singkat setelah load (pakai PAGE_WAIT_AFTER)
        await page.wait_for_timeout(int(PAGE_WAIT_AFTER * 1000))

        # --------------------------------------------------------
        # 🔎 Ambil semua selector pagination
        # --------------------------------------------------------
        selectors = [
            "li.b_pag nav[role='navigation'] ul.sb_pagF li a[href]",
            "ul.sb_pagF li a[href*='search?']",
        ]

        links = []
        for sel in selectors:
            found = await page.eval_on_selector_all(
                sel,
                "els => els.map(a => new URL(a.getAttribute('href'), window.location.origin).href)"
            )
            links.extend(found)

        # Hilangkan duplikat dan urutkan berdasarkan parameter first
        links = list(dict.fromkeys(links))
        links = sorted(
            links,
            key=lambda x: int(x.split("first=")[-1].split("&")[0]) if "first=" in x else 0,
        )

        # --------------------------------------------------------
        # ➕ Tambahkan halaman lanjutan sampai batas
        # --------------------------------------------------------
        if links:
            last_url = links[-1]
            extra_links = build_next_links(last_url, max_first=291, max_pere=28)
            for u in extra_links:
                if u not in links:
                    links.append(u)

        await context.close()
        await browser.close()
        return links


# ============================================================
# 💾 Fungsi penyimpan hasil
# ============================================================
def save_links(keyword: str, links: list[str]):
    output_dir = os.getenv("OUTPUT_DIR", "data/page")
    os.makedirs(output_dir, exist_ok=True)

    safe_kw_long = re.sub(r'[\\/*?:"<>|]', "", keyword).replace(" ", "_").replace(":", "").replace(".", "")
    safe_kw = safe_kw_long[:50]

    path = os.path.join(output_dir, f"pagination_{safe_kw}.csv")

    with open(path, "w", encoding="utf-8") as f:
        f.write("url\n")
        for link in links:
            f.write(f"{link}\n")

    print(f"✅ Saved {len(links)} pagination links to:\n{path}")
    return path


# ============================================================
# 🏁 Runner paralel untuk banyak keyword (menggunakan semaphore)
# ============================================================
async def run_keywords_parallel(keywords, headless=False):
    sem = asyncio.Semaphore(MAX_CONCURRENCY)

    async def worker(kw):
        async with sem:
            try:
                links = await get_bing_page_links(kw, headless=headless)
                save_links(kw, links)
            except Exception as e:
                print(f"[ERROR] keyword={kw} -> {e}")

    await asyncio.gather(*[worker(k) for k in keywords])


# ============================================================
# 🏁 Entry point
# ============================================================
if __name__ == "__main__":
    domains = [
    '"Kompas.com"','"Detik.com"','"Liputan6.com"','"Tempo.co"','"TribunNews.com"','"AntaraNews.com"','"kompasiana.com"','"Republika.co.id"'
    ]

    keywords_baru = [
        # TIK.DEV0901 – Chief Business Applications Officer
        "strategi pengembangan aplikasi bisnis",
        "tata kelola aplikasi enterprise",
        "penyelarasan aplikasi dengan proses bisnis"
    ]

    keywords = []
    for kw in keywords_baru:
        for d in domains:
            keywords.append(f"{kw} {d}")
        
    # jalankan paralel dengan batas MAX_CONCURRENCY
    asyncio.run(run_keywords_parallel(keywords, headless=True))
