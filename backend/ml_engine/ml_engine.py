from transformers import pipeline
from sentence_transformers import SentenceTransformer, util

# Only use pipelines that are supported in this transformers version
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
sentiment_model = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
similarity_model = SentenceTransformer("all-MiniLM-L6-v2")

def summarize(text):
    # Extractive summary - first 2 sentences, no model needed
    if not text:
        return ""
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if len(s.strip()) > 20]
    summary = ". ".join(sentences[:2])
    return summary[:300] if summary else text[:300]

def classify_difficulty(text):
    try:
        result = classifier(text[:512], candidate_labels=["Beginner", "Intermediate", "Advanced"])
        return result["labels"][0]
    except:
        return "Intermediate"

def generate_tags(text):
    try:
        result = classifier(text[:512], candidate_labels=["ML", "Web", "Automation", "API", "NLP", "Data", "Mobile", "Game"])
        return result["labels"][:3]
    except:
        return []

def analyze_sentiment(comments):
    if not comments:
        return 0.5
    try:
        scores = []
        for comment in comments[:5]:
            result = sentiment_model(comment[:512])
            label = result[0]["label"].lower()
            score = result[0]["score"]
            if "pos" in label:
                scores.append(score)
            elif "neg" in label:
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
