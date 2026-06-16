# AI-Powered Project Idea Discovery Platform

Discovers and ranks project ideas from HackerNews, Dev.to, GitHub, and Reddit using NLP models.

---

## Team
- BSAI24073
- BSAI24062

---

## Setup & Run

### 1. Install dependencies
```
pip install -r requirements.txt
```

### 2. Setup PostgreSQL
```sql
psql -U postgres
CREATE DATABASE idea_discovery;
\q
```

### 3. Configure environment
```
cp .env.example .env
# Edit .env and set your postgres password
```

### 4. Start Redis
```
sudo service redis-server start
redis-cli ping   # should return PONG
```

### 5. Run backend
```
python main.py
```
Backend runs at: http://localhost:8000

### 6. Open frontend
Open `frontend/ui.html` in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/search` | Search for ideas by keyword |
| GET | `/history` | Get all past sessions |
| GET | `/session/{id}` | Get ideas from a specific session |

### Example search request
```json
POST /search
{
  "query": "machine learning",
  "difficulty": "Beginner"
}
```

---

## Architecture

```
Frontend (ui.html)
     ↓ HTTP
FastAPI Backend
     ↓
Scraper → Cleaner → ML Engine → Ranker
  (4 sources)         (HuggingFace)
     ↓                      ↓
  Redis Cache          PostgreSQL DB
```

### Data Sources
- HackerNews (Show HN posts)
- Dev.to (articles by tag)
- GitHub (repositories by stars)
- Reddit (r/learnprogramming, r/SideProject)

### ML Models
- `facebook/bart-large-cnn` — summarization
- `facebook/bart-large-mnli` — difficulty classification + tag generation
- `cardiffnlp/twitter-roberta-base-sentiment-latest` — sentiment analysis
- `all-MiniLM-L6-v2` — duplicate detection via cosine similarity

### Ranking Formula
```
score = (upvotes × 0.4) + (comments × 0.2) + (sentiment × 0.3) + (recency × 0.1)
```

---

## Database Schema

**sessions** — stores each search query with timestamp  
**ideas** — stores ranked results linked to a session
