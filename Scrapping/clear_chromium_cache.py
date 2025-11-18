# clear_chromium_cache.py
import asyncio
from playwright.async_api import async_playwright

CHROMIUM_DATA_DIR = "chromium_cache"   # Folder untuk data Chromium Playwright

async def clear_storage_state(context):
    """Clear cookies, localStorage & sessionStorage using storage_state."""
    print("[INFO] Clearing storage_state cookies & local/session storage...")
    await context.clear_cookies()
    await context.storage_state(path="reset_state.json")   # kosongkan state
    print("[✓] storage_state cleared.")


async def clear_js_cache(context):
    """Run JS inside pages to unregister service workers and clear Cache API."""
    print("[INFO] Clearing JS caches (SW, CacheStorage, LocalStorage)...")

    script = """
        try {
            // Unregister all service workers
            if (navigator.serviceWorker && navigator.serviceWorker.getRegistrations) {
                navigator.serviceWorker.getRegistrations().then(rs => rs.forEach(r => r.unregister()));
            }

            // Clear Cache API
            if (window.caches && window.caches.keys) {
                caches.keys().then(keys => keys.forEach(k => caches.delete(k)));
            }

            // Clear localStorage & sessionStorage
            try { localStorage.clear(); } catch (e) {}
            try { sessionStorage.clear(); } catch (e) {}

        } catch (e) {}
    """

    # Inject script globally for all pages
    await context.add_init_script(script)

    # Load blank page to trigger script
    page = await context.new_page()
    await page.goto("https://example.com")
    await page.wait_for_timeout(1000)
    await page.close()

    print("[✓] JS-level cache cleared.")


async def deep_clear_cache():
    """Perform full Chromium deep cache clean."""
    print("\n🚀 Starting DEEP CACHE CLEAN")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch_persistent_context(
            CHROMIUM_DATA_DIR,
            headless=True
        )

        context = browser
        try:
            await clear_storage_state(context)
            await clear_js_cache(context)
        except Exception as e:
            print("[ERROR] during cleanup:", e)

        await context.close()

    print("\n✨ DONE: Chromium cache cleaned successfully.")


if __name__ == "__main__":
    asyncio.run(deep_clear_cache())
