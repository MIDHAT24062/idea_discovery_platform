from transformers import pipeline
from sentence_transformers import SentenceTransformer, util

# Lazy loading — models load only on first use, not at startup
_classifier = None
_sentiment_model = None
_similarity_model = None

def get_classifier():
    global _classifier
    if _classifier is None:
        # ~90MB instead of 1.6GB — same zero-shot classification
        _classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")
    return _classifier

def get_sentiment_model():
    global _sentiment_model
    if _sentiment_model is None:
        # ~65MB instead of 500MB
        _sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    return _sentiment_model

def get_similarity_model():
    global _similarity_model
    if _similarity_model is None:
        # already small, keeping it
        _similarity_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _similarity_model


def summarize(text):
    if not text:
        return ""
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 20]
    summary = ". ".join(sentences[:2])
    return summary[:300] if summary else text[:300]

def classify_difficulty(text):
    try:
        result = get_classifier()(text[:512], candidate_labels=["Beginner", "Intermediate", "Advanced"])
        return result["labels"][0]
    except:
        return "Intermediate"

def generate_tags(text):
    try:
        result = get_classifier()(text[:512], candidate_labels=["ML", "Web", "Automation", "API", "NLP", "Data", "Mobile", "Game"])
        return result["labels"][:3]
    except:
        return []

def analyze_sentiment(comments):
    if not comments:
        return 0.5
    try:
        scores = []
        for comment in comments[:5]:
            result = get_sentiment_model()(comment[:512])
            label = result[0]["label"].lower()
            score = result[0]["score"]
            if "pos" in label or label == "positive":
                scores.append(score)
            elif "neg" in label or label == "negative":
                scores.append(1 - score)
            else:
                scores.append(0.5)
        return sum(scores) / len(scores)
    except:
        return 0.5

def process_posts(cleaned_posts):
    enriched = []
    for post in cleaned_posts:
        summary = summarize(post["body"])
        difficulty = classify_difficulty(post["title"] + " " + post["body"])
        tags = generate_tags(post["body"])
        sentiment_score = analyze_sentiment(post["comments"])
        enriched.append({
            "title": post["title"],
            "summary": summary,
            "difficulty": difficulty,
            "tags": tags,
            "sentiment_score": sentiment_score,
            "upvotes": post["upvotes"],
            "source": post["source"],
            "url": post["url"],
            "posted_at": post["posted_at"]
        })
    return enriched
