from backend.database.models import SessionLocal, Idea, Session, User
from datetime import datetime


# ── User operations ──────────────────────────────────────────────────────────

def create_user(user_id: str, username: str, email: str, password_hash: str) -> User:
    db = SessionLocal()
    try:
        user = User(id=user_id, username=username, email=email, password_hash=password_hash)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def get_user_by_id(user_id: str) -> User | None:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def get_user_by_username_or_email(ident: str) -> User | None:
    """Look up by username OR email (for login)."""
    db = SessionLocal()
    try:
        return (
            db.query(User)
            .filter((User.username == ident) | (User.email == ident))
            .first()
        )
    finally:
        db.close()


def username_exists(username: str) -> bool:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.username == username).first() is not None
    finally:
        db.close()


def email_exists(email: str) -> bool:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.email == email).first() is not None
    finally:
        db.close()


# ── Session operations ───────────────────────────────────────────────────────

def save_session(session_id: str, query: str, ideas: list, user_id: str | None = None):
    db = SessionLocal()
    try:
        session = Session(id=session_id, query=query, timestamp=datetime.utcnow(), user_id=user_id)
        db.add(session)
        db.flush()  # write session row to DB before inserting ideas (FK constraint)
        for idea in ideas:
            tags_val = idea.get("tags", [])
            if isinstance(tags_val, list):
                tags_val = ", ".join(tags_val)
            db_idea = Idea(
                session_id=session_id,
                title=str(idea.get("title", "") or "")[:500],
                summary=str(idea.get("summary", "") or "")[:2000],
                difficulty=str(idea.get("difficulty", "") or "")[:50],
                tags=str(tags_val or "")[:500],
                score=float(idea.get("score") or 0.0),
                source=str(idea.get("source", "") or "")[:100],
                url=str(idea.get("url", "") or "")[:1000],
                sentiment_score=float(idea.get("sentiment_score") or 0.0),
                upvotes=int(idea.get("upvotes") or 0),
            )
            db.add(db_idea)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"save_session ERROR: {type(e).__name__}: {e}")
        raise  # re-raise so search endpoint catches it and returns real error
    finally:
        db.close()


def get_all_sessions(user_id: str | None = None):
    """Return sessions. If user_id provided, scoped to that user."""
    db = SessionLocal()
    try:
        q = db.query(Session)
        if user_id:
            q = q.filter(Session.user_id == user_id)
        sessions = q.order_by(Session.timestamp.desc()).all()
        return [
            {"session_id": s.id, "query": s.query, "timestamp": str(s.timestamp)}
            for s in sessions
        ]
    finally:
        db.close()


def get_session(session_id: str, user_id: str | None = None) -> dict | None:
    db = SessionLocal()
    try:
        q = db.query(Session).filter(Session.id == session_id)
        if user_id:
            q = q.filter(Session.user_id == user_id)
        session = q.first()
        if not session:
            return None
        ideas = db.query(Idea).filter(Idea.session_id == session_id).all()
        return {
            "session_id": session_id,
            "query": session.query,
            "timestamp": str(session.timestamp),
            "ideas": [
                {
                    "title": i.title,
                    "summary": i.summary,
                    "difficulty": i.difficulty,
                    "tags": i.tags.split(", ") if i.tags else [],
                    "score": i.score,
                    "source": i.source,
                    "url": i.url,
                    "sentiment_score": i.sentiment_score,
                    "upvotes": i.upvotes,
                }
                for i in ideas
            ],
        }
    finally:
        db.close()


def delete_session(session_id: str, user_id: str | None = None) -> bool:
    """Delete session and its ideas. Returns True if deleted, False if not found/unauthorized."""
    db = SessionLocal()
    try:
        q = db.query(Session).filter(Session.id == session_id)
        if user_id:
            q = q.filter(Session.user_id == user_id)
        session = q.first()
        if not session:
            return False
        db.query(Idea).filter(Idea.session_id == session_id).delete()
        db.delete(session)
        db.commit()
        return True
    finally:
        db.close()
