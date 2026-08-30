# Idea Discovery Platform

An intelligent project idea discovery platform that collects project ideas and discussions from multiple online sources, processes them using lightweight NLP techniques, removes duplicates, and ranks results based on multiple signals.

## Features

* Search project ideas across multiple platforms
* Data collection from Hacker News, Dev.to, GitHub, and Reddit
* Asynchronous/concurrent API requests
* Lightweight extractive text summarization
* Automatic topic tagging
* Rule-based difficulty classification
* Lexicon-based sentiment scoring
* Duplicate detection using Jaccard similarity
* Multi-factor idea ranking
* PostgreSQL for users and search history
* Redis caching for repeated searches
* JWT-based authentication
* Search history and saved sessions

## Architecture

```text
User Query
    ↓
FastAPI Backend
    ↓
Concurrent Data Collection
    ↓
Hacker News / Dev.to / GitHub / Reddit
    ↓
Data Cleaning & NLP Processing
    ↓
Summarization + Tagging + Difficulty + Sentiment
    ↓
Duplicate Detection
    ↓
Idea Ranking
    ↓
PostgreSQL + Redis
    ↓
Web Frontend
```

## NLP & Ranking

The current version uses lightweight techniques instead of large pretrained models:

* Summarization: Extractive sentence selection
* Topic Tagging: Keyword-based classification
* Difficulty: Keyword-based scoring
* Sentiment: Lexicon-based sentiment scoring
* Duplicate Detection: Jaccard similarity between title terms
* Ranking: Combination of engagement, sentiment, and recency

This lightweight approach keeps the application small and easier to deploy without requiring PyTorch, Transformers, or GPU inference.

## Tech Stack

**Backend:** Python, FastAPI, SQLAlchemy, Uvicorn
**Database:** PostgreSQL
**Caching:** Redis
**HTTP/API:** HTTPX
**Frontend:** HTML, CSS, JavaScript
**Authentication:** JWT + PBKDF2-HMAC-SHA256

## Project Structure

```text
idea_discovery_platform/
├── backend/
│   ├── auth/
│   ├── db/
│   ├── ml_engine/
│   ├── ranker/
│   ├── scrapers/
│   └── main.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── requirements.txt
└── README.md
```

## Installation

```bash
git clone <repository-url>
cd idea_discovery_platform

python -m venv venv
venv\Scripts\activate        # Windows

pip install -r requirements.txt
```

Create a `.env` file:

```env
DATABASE_URL=postgresql://username:password@localhost/idea_discovery
SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379
```

Run the backend:

```bash
uvicorn backend.main:app --reload
```

API documentation:

```text
http://localhost:8000/docs
```

## Project Evolution

The project initially experimented with larger Hugging Face NLP models. Due to model size and deployment constraints, the current implementation was redesigned around lightweight NLP and heuristic techniques.

This reduced the dependency footprint and made the application easier to deploy on resource-constrained environments.

## Contributors

**Midhat Fatima** — BS Artificial Intelligence, ITU
**Samar Tahir** — BS Artificial Intelligence, ITU

**Student IDs:** BS AI24062, BS AI24073

## Project Type

University Project — BS Artificial Intelligence
