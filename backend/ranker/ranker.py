from sentence_transformers import SentenceTransformer, util
from datetime import datetime

# Load lazily so startup doesn't block/crash on Railway cold boot
_similarity_model = None


def get_similarity_model():
    global _similarity_model
    if _similarity_model is None:
        _similarity_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _similarity_model


def normalize(values: list) -> list:
    if not values:
        return []
    min_val = min(values)
    max_val = max(values)
    if max_val == min_val:
        return [0.5 for _ in values]
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


def remove_duplicates(ideas: list, threshold: float = 0.85) -> list:
    if not ideas:
        return ideas
    model = get_similarity_model()
    summaries = [i["summary"] for i in ideas]
    embeddings = model.encode(summaries)
    kept = []
    for i in range(len(ideas)):
        is_duplicate = False
        for j in kept:
            sim = util.cos_sim(embeddings[i], embeddings[j]).item()
            if sim > threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            kept.append(i)
    return [ideas[i] for i in kept]


def rank(enriched_ideas: list) -> list:
    if not enriched_ideas:
        return []

    upvotes = normalize([i["upvotes"] for i in enriched_ideas])
    comments = normalize([len(i.get("comments", [])) for i in enriched_ideas])

    for idx, idea in enumerate(enriched_ideas):
        recency = compute_recency(idea["posted_at"])
        score = (
            upvotes[idx] * 0.4
            + comments[idx] * 0.2
            + idea["sentiment_score"] * 0.3
            + recency * 0.1
        )
        idea["score"] = round(score * 100, 1)

    deduplicated = remove_duplicates(enriched_ideas)
    return sorted(deduplicated, key=lambda x: x["score"], reverse=True)
