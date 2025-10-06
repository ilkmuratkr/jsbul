import asyncio
from typing import Iterable, Dict, Any, List
from playwright.async_api import async_playwright
from .matcher import matches_any_domain


DEFAULT_WAIT_UNTIL = "networkidle"
PAGE_TIMEOUT_MS = 40000
NETWORK_IDLE_EXTRA_MS = 3000


async def scan_single(
    url: str,
    target_domains: Iterable[str],
    *,
    page_timeout_ms: int = PAGE_TIMEOUT_MS,
    extra_wait_ms: int = NETWORK_IDLE_EXTRA_MS,
    verbose: bool = False,
) -> Dict[str, Any]:
    hits: Dict[str, str] = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        if verbose:
            print(f"[START] {url}")

        def on_request(req):
            try:
                rt = req.resource_type
                u = req.url
                is_js = rt == "script" or (rt in {"xhr", "fetch"} and u.lower().endswith(".js"))
                if not is_js:
                    return
                matched = matches_any_domain(u, target_domains)
                if matched:
                    hits[u] = matched
            except Exception:
                pass

        page.on("request", on_request)

        try:
            await page.goto(url, wait_until=DEFAULT_WAIT_UNTIL, timeout=page_timeout_ms)
            await page.wait_for_timeout(extra_wait_ms)
            # DOM'daki script[src] eldesi
            scripts: List[str] = await page.evaluate(
                """() => Array.from(document.querySelectorAll('script[src]')).map(s => s.src)"""
            )
            for s in scripts:
                matched = matches_any_domain(s, target_domains)
                if matched:
                    hits[s] = matched
            if verbose and len(hits) > 0:
                print(f"[DONE]  {url} | matches={len(hits)}")
        finally:
            await context.close()
            await browser.close()

    return {
        "url": url,
        "matched": len(hits) > 0,
        "matches": [{"request_url": u, "domain": d} for u, d in hits.items()],
    }


async def scan_many(
    urls: Iterable[str],
    target_domains: Iterable[str],
    concurrency: int = 5,
    *,
    page_timeout_ms: int = PAGE_TIMEOUT_MS,
    extra_wait_ms: int = NETWORK_IDLE_EXTRA_MS,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    sem = asyncio.Semaphore(concurrency)

    async def _wrapped(u: str):
        async with sem:
            try:
                return await scan_single(
                    u,
                    target_domains,
                    page_timeout_ms=page_timeout_ms,
                    extra_wait_ms=extra_wait_ms,
                    verbose=verbose,
                )
            except Exception as e:
                if verbose:
                    print(f"[ERROR] {u} | {e}")
                return {"url": u, "matched": False, "matches": [], "error": str(e)}

    tasks = [asyncio.create_task(_wrapped(u)) for u in urls]
    return await asyncio.gather(*tasks)


