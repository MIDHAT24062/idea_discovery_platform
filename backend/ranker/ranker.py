"""
Lightweight ranker — no sentence-transformers, no torch.
Deduplication uses simple title-word overlap instead of embeddings.
"""

from datetime import datetime


def normalize(values: list) -> list:
    if not values:
        return []
    min_val = min(values)
    max_val = max(values)
    if max_val == min_val:
        return [0.5] * len(values)
    return [(v - min_val) / (max_val - min_val) for v in values]


def compute_recency(posted_at) -> float:
    try:
        if isinstance(posted_at, str):
            posted_at = posted_at[:10]
            posted_date = datetime.strptime(posted_at, "%Y-%m-%d")
        else:
            posted_date = posted_at
        days_old = (datetime.utcnow() - posted_date).days
        return max(0.0, 1.0 - (days_old / 30))
    except Exception:
        return 0.5


def _title_words(title: str) -> set:
    stopwords = {"a", "an", "the", "to", "of", "in", "for", "on", "with", "and", "or", "is", "how"}
    return {w.lower() for w in title.split() if w.lower() not in stopwords and len(w) > 2}


def remove_duplicates(ideas: list, threshold: float = 0.6) -> list:
    """Remove near-duplicate titles using word-overlap Jaccard similarity."""
    kept_indices = []
    kept_word_sets = []
    for i, idea in enumerate(ideas):
        words = _title_words(idea["title"])
        is_duplicate = False
        for kept_words in kept_word_sets:
            union = words | kept_words
            if not union:
                continue
            jaccard = len(words & kept_words) / len(union)
            if jaccard >= threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            kept_indices.append(i)
            kept_word_sets.append(words)
    return [ideas[i] for i in kept_indices]


def rank(enriched_ideas: list) -> list:
    if not enriched_ideas:
        return []

    upvotes_norm  = normalize([i["upvotes"] for i in enriched_ideas])
    comments_norm = normalize([len(i.get("comments", [])) for i in enriched_ideas])

    for idx, idea in enumerate(enriched_ideas):
        recency = compute_recency(idea["posted_at"])
        score = (
            upvotes_norm[idx]  * 0.4
            + comments_norm[idx] * 0.2
            + idea["sentiment_score"] * 0.3
            + recency * 0.1
        )
        idea["score"] = round(score * 100, 1)

    deduplicated = remove_duplicates(enriched_ideas)
    return sorted(deduplicated, key=lambda x: x["score"], reverse=True)
