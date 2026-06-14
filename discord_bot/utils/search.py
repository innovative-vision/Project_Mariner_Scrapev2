"""
Search provider abstraction.
Switch between Serper.dev and Google Custom Search via SEARCH_PROVIDER in .env.
"""
from __future__ import annotations
import aiohttp
from config import Config


async def search_google(query: str, num_results: int = 10) -> list[dict]:
    """
    Returns up to `num_results` dicts:
      { title, url, snippet, image }  — image is None for results 2-10
    """
    match Config.SEARCH_PROVIDER:
        case "serper":
            return await _serper_search(query, num_results)
        case "google_cse":
            return await _google_cse_search(query, num_results)
        case _:
            raise ValueError(
                f"Unknown SEARCH_PROVIDER: {Config.SEARCH_PROVIDER!r}. "
                "Choose 'serper' or 'google_cse'."
            )


async def _serper_search(query: str, num: int) -> list[dict]:
    """
    Serper.dev — recommended.
    Sign up at https://serper.dev  (free trial, then ~$50 for 50k searches).
    Returns real Google results including knowledge graph images.
    """
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": Config.SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": num}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()

    # Best-effort image for the first result
    kg = data.get("knowledgeGraph", {})
    images = data.get("images", [])
    top_image: str | None = kg.get("imageUrl") or (images[0].get("imageUrl") if images else None)

    results: list[dict] = []
    for i, item in enumerate(data.get("organic", [])[:num]):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "image": top_image if i == 0 else None,
        })
    return results


async def _google_cse_search(query: str, num: int) -> list[dict]:
    """
    Google Custom Search JSON API.
    Set up at https://programmablesearchengine.google.com  (100 free/day).
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
            pagemap = item.get("pagemap", {})
            cse_images = pagemap.get("cse_image", [])
            image = cse_images[0].get("src") if cse_images else None
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "image": image,
        })
    return results
