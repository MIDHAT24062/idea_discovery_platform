import requests
from datetime import datetime

def fetch_hackernews(query, limit=10):
    posts = []
    try:
        url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=show_hn&hitsPerPage={limit}"
        response = requests.get(url, timeout=10)
        data = response.json()
        for hit in data.get("hits", []):
            posts.append({
                "title": hit.get("title", ""),
                "body": hit.get("story_text") or hit.get("title", ""),
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                "upvotes": hit.get("points") or 0,
                "comments": [],
                "source": "HackerNews",
                "posted_at": hit.get("created_at", str(datetime.utcnow()))
            })
    except Exception as e:
        print(f"HackerNews error: {e}")
    return posts

def fetch_devto(query, limit=10):
    posts = []
    try:
        url = f"https://dev.to/api/articles?tag={query}&per_page={limit}"
        response = requests.get(url, timeout=10)
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
                "posted_at": article.get("published_at", str(datetime.utcnow()))
            })
    except Exception as e:
        print(f"DevTo error: {e}")
    return posts

def fetch_github(query, limit=10):
    posts = []
    try:
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={limit}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        for repo in data.get("items", []):
            posts.append({
                "title": repo.get("name", ""),
                "body": repo.get("description") or repo.get("name", ""),
                "url": repo.get("html_url", ""),
                "upvotes": repo.get("stargazers_count") or 0,
                "comments": [],
                "source": "GitHub",
                "posted_at": repo.get("created_at", str(datetime.utcnow()))
            })
    except Exception as e:
        print(f"GitHub error: {e}")
    return posts

def fetch_reddit(query, limit=10):
    posts = []
    try:
        url = f"https://www.reddit.com/r/learnprogramming+cscareerquestions+SideProject/search.json?q={query}&sort=top&limit={limit}&t=year"
        headers = {"User-Agent": "IdeaDiscoveryBot/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
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
                "posted_at": str(datetime.utcfromtimestamp(p.get("created_utc", 0)))
            })
    except Exception as e:
        print(f"Reddit error: {e}")
    return posts

def fetch_all(query, limit=10):
    posts = []
    posts += fetch_hackernews(query, limit)
    posts += fetch_devto(query, limit)
    posts += fetch_github(query, limit)
    posts += fetch_reddit(query, limit)
    return posts
