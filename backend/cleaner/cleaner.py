def clean_posts(posts):
    cleaned = []
    for post in posts:
        title = post.get("title", "").strip()
        body = post.get("body", "").strip()

        if not title:
            continue
        if len(body) < 10:
            body = title
        
        body = body.replace("<p>", " ").replace("</p>", " ")
        body = body.replace("<li>", " ").replace("</li>", " ")
        body = body.replace("<ul>", " ").replace("</ul>", " ")
        body = body.replace("<br>", " ").replace("<br/>", " ")

        cleaned.append({
            "title": title,
            "body": body[:1000],
            "url": post.get("url", ""),
            "upvotes": post.get("upvotes", 0),
            "comments": post.get("comments", []),
            "source": post.get("source", ""),
            "posted_at": post.get("posted_at", "")
        })
    return cleaned