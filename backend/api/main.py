import os
import json
import uuid

import redis
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from backend.database.models import init_db
from backend.database.db_operations import (
    create_user, get_user_by_id, get_user_by_username_or_email,
    username_exists, email_exists,
    save_session, get_all_sessions, get_session, delete_session,
)
from backend.auth.auth_utils import hash_password, verify_password, create_token, decode_token
from backend.scraper.scraper import fetch_all          # now async
from backend.cleaner.cleaner import clean_posts
from backend.ml_engine.ml_engine import process_posts
from backend.ranker.ranker import rank

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(title="IDP – Idea Discovery Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Redis (optional cache) ────────────────────────────────────────────────────

redis_url = os.getenv("REDIS_URL", "")
try:
    if redis_url:
        cache = redis.Redis.from_url(redis_url, decode_responses=True)
        cache.ping()
        CACHE_ENABLED = True
        print("✅ Redis connected")
    else:
        CACHE_ENABLED = False
        cache = None
        print("⚠️  No REDIS_URL — caching disabled")
except Exception as e:
    CACHE_ENABLED = False
    cache = None
    print(f"⚠️  Redis unavailable ({e}) — caching disabled")

# ── Database ──────────────────────────────────────────────────────────────────

init_db()

# ── Auth helpers ──────────────────────────────────────────────────────────────

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload["sub"]


def optional_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str | None:
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    return payload["sub"] if payload else None


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class SearchRequest(BaseModel):
    query: str
    difficulty: str = "all"


# ── Auth endpoints ────────────────────────────────────────────────────────────

@app.post("/auth/register", status_code=201)
def register(req: RegisterRequest):
    username = req.username.strip()
    email = req.email.strip().lower()
    password = req.password

    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="All fields are required.")
    if len(username) < 3 or len(username) > 30:
        raise HTTPException(status_code=400, detail="Username must be 3–30 characters.")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    if username_exists(username):
        raise HTTPException(status_code=409, detail="Username already taken.")
    if email_exists(email):
        raise HTTPException(status_code=409, detail="Email already registered.")

    user_id = str(uuid.uuid4())
    password_hash = hash_password(password)
    user = create_user(user_id, username, email, password_hash)

    token = create_token(user.id, user.username)
    return {
        "token": token,
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }


@app.post("/auth/login")
def login(req: LoginRequest):
    ident = req.username_or_email.strip()
    user = get_user_by_username_or_email(ident)
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username/email or password.")

    token = create_token(user.id, user.username)
    return {
        "token": token,
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }


@app.post("/auth/logout")
def logout(user_id: str = Depends(get_current_user_id)):
    return {"detail": "Logged out."}


@app.get("/auth/me")
def me(user_id: str = Depends(get_current_user_id)):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"id": user.id, "username": user.username, "email": user.email}


# ── Search ────────────────────────────────────────────────────────────────────

@app.post("/search")
async def search(
    request: SearchRequest,
    user_id: str | None = Depends(optional_user_id),
):
    cache_key = f"search:{request.query}:{request.difficulty}"

    # Try cache first
    if CACHE_ENABLED:
        try:
            cached = cache.get(cache_key)
            if cached:
                data = json.loads(cached)
                new_session_id = str(uuid.uuid4())
                save_session(new_session_id, request.query, data["ideas"], user_id=user_id)
                return {"session_id": new_session_id, "ideas": data["ideas"]}
        except Exception:
            pass

    # fetch_all is now truly async — no event loop blocking
    raw_posts = await fetch_all(request.query)
    cleaned = clean_posts(raw_posts)
    enriched = process_posts(cleaned)
    ranked = rank(enriched)

    if request.difficulty != "all":
        ranked = [i for i in ranked if i["difficulty"].lower() == request.difficulty.lower()]

    session_id = str(uuid.uuid4())
    save_session(session_id, request.query, ranked, user_id=user_id)

    result = {"session_id": session_id, "ideas": ranked}

    if CACHE_ENABLED:
        try:
            cache.setex(cache_key, 600, json.dumps(result))
        except Exception:
            pass

    return result


# ── History ───────────────────────────────────────────────────────────────────

@app.get("/history")
def get_history(user_id: str = Depends(get_current_user_id)):
    sessions = get_all_sessions(user_id=user_id)
    return {"sessions": sessions}


# ── Session ───────────────────────────────────────────────────────────────────

@app.get("/session/{session_id}")
def get_session_by_id(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
):
    session = get_session(session_id, user_id=user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session


@app.delete("/session/{session_id}", status_code=200)
def delete_session_by_id(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
):
    deleted = delete_session(session_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found or not yours.")
    return {"detail": "Session deleted."}
