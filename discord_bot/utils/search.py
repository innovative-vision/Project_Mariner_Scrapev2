"""
Search provider abstraction.
Default: Brave Search API  — 2,000 free requests/month, no credit card required.
Alternative: Google Custom Search JSON API  — 100 free requests/day.
"""
from __future__ import annotations
import aiohttp
from config import Config


async def search_google(query: str, num_results: int = 10) -> list[dict]:
    """
    Returns up to `num_results` dicts:
      { title, url, snippet, image }  — image only populated for result #1
    """
    match Config.SEARCH_PROVIDER:
        case "brave":
            return await _brave_search(query, num_results)
        case "google_cse":
            return await _google_cse_search(query, num_results)
        case _:
            raise ValueError(
                f"Unknown SEARCH_PROVIDER: {Config.SEARCH_PROVIDER!r}. "
                "Choose 'brave' or 'google_cse'."
            )


async def _brave_search(query: str, num: int) -> list[dict]:
    """
    Brave Search API  — https://api.search.brave.com
    Free tier: 2,000 requests/month, no credit card required.
    Sign up and grab your key at https://api.search.brave.com/app/keys
    """
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": Config.BRAVE_API_KEY,
    }
    params = {"q": query, "count": min(num, 20)}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

    results: list[dict] = []
    for i, item in enumerate(data.get("web", {}).get("results", [])[:num]):
        thumbnail = item.get("thumbnail", {}) or {}
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("description", ""),
            "image": thumbnail.get("src") if i == 0 and thumbnail else None,
        })
    return results


async def _google_cse_search(query: str, num: int) -> list[dict]:
    """
    Google Custom Search JSON API  — 100 free requests/day.
    Setup: https://programmablesearchengine.google.com
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": Config.GOOGLE_CSE_API_KEY,
        "cx": Config.GOOGLE_CSE_ID,
        "q": query,
        "num": min(num, 10),
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            data = await resp.json()

    results: list[dict] = []
    for i, item in enumerate(data.get("items", [])[:num]):
        image: str | None = None
        if i == 0:
            cse_images = item.get("pagemap", {}).get("cse_image", [])
            image = cse_images[0].get("src") if cse_images else None
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "image": image,
        })
    return results
