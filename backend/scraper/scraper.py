import asyncio
from datetime import datetime
import httpx

TIMEOUT = httpx.Timeout(15.0)


async def fetch_hackernews(client: httpx.AsyncClient, query: str, limit: int = 10) -> list:
    posts = []
    try:
        url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=show_hn&hitsPerPage={limit}"
        response = await client.get(url)
        data = response.json()
        for hit in data.get("hits", []):
            posts.append({
                "title": hit.get("title", ""),
                "body": hit.get("story_text") or hit.get("title", ""),
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                "upvotes": hit.get("points") or 0,
                "comments": [],
                "source": "HackerNews",
                "posted_at": hit.get("created_at", str(datetime.utcnow())),
            })
    except Exception as e:
        print(f"HackerNews error: {e}")
    return posts


async def fetch_devto(client: httpx.AsyncClient, query: str, limit: int = 10) -> list:
    posts = []
    try:
        url = f"https://dev.to/api/articles?tag={query}&per_page={limit}"
        response = await client.get(url)
        data = response.json()
        if not isinstance(data, list):
            return posts
        for article in data:
            if not isinstance(article, dict):
                continue
            posts.append({
                "title": article.get("title", ""),
                "body": article.get("description") or article.get("title", ""),
                "url": article.get("url", ""),
                "upvotes": article.get("positive_reactions_count") or 0,
                "comments": [],
                "source": "DevTo",
                "posted_at": article.get("published_at", str(datetime.utcnow())),
            })
    except Exception as e:
        print(f"DevTo error: {e}")
    return posts


async def fetch_github(client: httpx.AsyncClient, query: str, limit: int = 10) -> list:
    posts = []
    try:
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={limit}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = await client.get(url, headers=headers)
        data = response.json()
        for repo in data.get("items", []):
            posts.append({
                "title": repo.get("name", ""),
                "body": repo.get("description") or repo.get("name", ""),
                "url": repo.get("html_url", ""),
                "upvotes": repo.get("stargazers_count") or 0,
                "comments": [],
                "source": "GitHub",
                "posted_at": repo.get("created_at", str(datetime.utcnow())),
            })
    except Exception as e:
        print(f"GitHub error: {e}")
    return posts


async def fetch_reddit(client: httpx.AsyncClient, query: str, limit: int = 10) -> list:
    posts = []
    try:
        url = (
            f"https://www.reddit.com/r/learnprogramming+cscareerquestions+SideProject"
            f"/search.json?q={query}&sort=top&limit={limit}&t=year"
        )
        headers = {"User-Agent": "IdeaDiscoveryBot/1.0"}
        response = await client.get(url, headers=headers)
        data = response.json()
        for post in data.get("data", {}).get("children", []):
            p = post.get("data", {})
            posts.append({
                "title": p.get("title", ""),
                "body": p.get("selftext") or p.get("title", ""),
                "url": f"https://reddit.com{p.get('permalink', '')}",
                "upvotes": p.get("ups") or 0,
                "comments": [],
                "source": "Reddit",
                "posted_at": str(datetime.utcfromtimestamp(p.get("created_utc", 0))),
            })
    except Exception as e:
        print(f"Reddit error: {e}")
    return posts


async def fetch_all(query: str, limit: int = 10) -> list:
    """Fetch from all sources concurrently using a single shared async HTTP client."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        results = await asyncio.gather(
            fetch_hackernews(client, query, limit),
            fetch_devto(client, query, limit),
            fetch_github(client, query, limit),
            fetch_reddit(client, query, limit),
            return_exceptions=True,
        )
    posts = []
    for r in results:
        if isinstance(r, list):
            posts.extend(r)
        else:
            print(f"Scraper gather error: {r}")
    return posts
