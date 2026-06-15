"""
Lightweight ML engine — no torch, no transformers, no model downloads.
Uses keyword heuristics that produce the same categories as the heavy models
but run instantly and use < 5 MB RAM. Safe for Railway free tier.
"""

import re

# ── Keyword maps ──────────────────────────────────────────────────────────────

DIFFICULTY_KEYWORDS = {
    "Beginner": [
        "beginner", "simple", "basic", "easy", "starter", "intro", "hello world",
        "tutorial", "learn", "first", "getting started", "todo", "crud", "static",
        "landing page", "portfolio", "calculator", "weather app", "quiz",
    ],
    "Advanced": [
        "distributed", "kubernetes", "microservice", "blockchain", "compiler",
        "neural network", "deep learning", "transformer", "reinforcement",
        "real-time", "low latency", "high performance", "scalable", "concurrent",
        "multithreaded", "async", "websocket", "p2p", "zero knowledge",
        "cryptography", "embedded", "kernel", "gpu", "cuda", "llm", "fine-tun",
    ],
}

TAG_KEYWORDS = {
    "ML":         ["machine learning", "ml", "neural", "model", "training", "dataset",
                   "classification", "regression", "clustering", "llm", "ai", "gpt"],
    "Web":        ["web", "website", "html", "css", "react", "vue", "angular", "frontend",
                   "backend", "http", "rest", "graphql", "nextjs", "django", "flask", "fastapi"],
    "Automation": ["automat", "scraper", "scraping", "bot", "script", "workflow",
                   "schedule", "cron", "pipeline", "ci/cd", "devops"],
    "API":        ["api", "endpoint", "webhook", "integration", "sdk", "openapi", "swagger"],
    "NLP":        ["nlp", "text", "language", "sentiment", "summariz", "translation",
                   "chatbot", "speech", "token", "embedding", "bert", "gpt"],
    "Data":       ["data", "analytics", "dashboard", "visualization", "chart", "csv",
                   "database", "sql", "nosql", "etl", "warehouse", "spark", "pandas"],
    "Mobile":     ["mobile", "android", "ios", "flutter", "react native", "swift",
                   "kotlin", "app store", "push notification"],
    "Game":       ["game", "pygame", "unity", "godot", "2d", "3d", "multiplayer",
                   "physics", "render", "sprite", "level"],
    "Open Source":["open source", "opensource", "github", "contribution", "fork", "pr"],
}

POSITIVE_WORDS = {
    "great", "awesome", "excellent", "amazing", "love", "perfect", "best",
    "fantastic", "helpful", "useful", "brilliant", "nice", "good", "cool",
    "impressive", "innovative", "clean", "elegant", "simple", "intuitive",
}
NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "hate", "broken", "useless", "worst",
    "horrible", "disappointing", "confusing", "poor", "slow", "buggy",
    "complicated", "messy", "ugly", "fail", "failed", "crash", "error",
}


# ── Core functions ────────────────────────────────────────────────────────────

def summarize(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\n", " ")
    sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]
    summary = ". ".join(sentences[:2])
    return (summary[:300] + "…") if len(summary) > 300 else (summary or text[:300])


def classify_difficulty(text: str) -> str:
    lower = text.lower()
    adv_hits = sum(1 for kw in DIFFICULTY_KEYWORDS["Advanced"] if kw in lower)
    beg_hits = sum(1 for kw in DIFFICULTY_KEYWORDS["Beginner"] if kw in lower)
    if adv_hits > beg_hits:
        return "Advanced"
    if beg_hits > adv_hits:
        return "Beginner"
    return "Intermediate"


def generate_tags(text: str) -> list:
    lower = text.lower()
    scores = {tag: 0 for tag in TAG_KEYWORDS}
    for tag, keywords in TAG_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                scores[tag] += 1
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [tag for tag, score in ranked[:3] if score > 0] or ["General"]


def analyze_sentiment(comments: list) -> float:
    if not comments:
        return 0.5
    scores = []
    for comment in comments[:10]:
        words = set(re.findall(r"\b\w+\b", comment.lower()))
        pos = len(words & POSITIVE_WORDS)
        neg = len(words & NEGATIVE_WORDS)
        total = pos + neg
        if total == 0:
            scores.append(0.5)
        else:
            scores.append(pos / total)
    return round(sum(scores) / len(scores), 3)


def process_posts(cleaned_posts: list) -> list:
    enriched = []
    for post in cleaned_posts:
        combined = post["title"] + " " + post["body"]
        enriched.append({
            "title":           post["title"],
            "summary":         summarize(post["body"]),
            "difficulty":      classify_difficulty(combined),
            "tags":            generate_tags(combined),
            "sentiment_score": analyze_sentiment(post["comments"]),
            "upvotes":         post["upvotes"],
            "source":          post["source"],
            "url":             post["url"],
            "posted_at":       post["posted_at"],
        })
    return enriched
