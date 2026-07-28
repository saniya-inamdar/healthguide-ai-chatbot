from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai import generate_reply
from app.config import get_settings
from app.database import Base, engine, get_db
from app.models import ChatMessage, User
from app.schemas import ChatRequest, ChatResponse, LoginRequest, MessageResponse, RegisterRequest, TokenResponse
from app.security import create_access_token, get_current_user, hash_password, verify_password

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="HealthGuide AI", docs_url=None if settings.environment == "production" else "/docs")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/", include_in_schema=False)
def serve_homepage() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    user = User(name=payload.name.strip(), email=payload.email.lower(), password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    return TokenResponse(access_token=create_access_token(user.id), name=user.name)


@app.post("/api/auth/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return TokenResponse(access_token=create_access_token(user.id), name=user.name)


@app.get("/api/history", response_model=list[MessageResponse])
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    messages = db.scalars(select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.created_at.desc()).limit(30)).all()
    return list(reversed(messages))


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("15/minute")
def chat(request: Request, payload: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    previous = db.scalars(select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.created_at.desc()).limit(12)).all()
    history_messages = [{"role": item.role, "content": item.content} for item in reversed(previous)]
    try:
        reply = generate_reply(payload.message.strip(), history_messages)
    except Exception:
        raise HTTPException(status_code=503, detail="The AI service is temporarily unavailable. Please try again shortly.")

    db.add_all([
        ChatMessage(user_id=user.id, role="user", content=payload.message.strip()),
        ChatMessage(user_id=user.id, role="assistant", content=reply),
    ])
    db.commit()
    return ChatResponse(reply=reply)
