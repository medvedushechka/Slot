import os
from typing import List
import json
from datetime import datetime
import hashlib
import secrets

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Base, engine, get_db, SessionLocal
from models import User, Spin, SessionData, ProvablyFairState
from slot_engine import provably_fair_spin_reels, calculate_win
from slot_services import (
    get_reels_matrix_for_bet,
    acquire_spin_lock,
    release_spin_lock,
)
from integrations import get_redis, publish_spin_event

# Password hashing
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

# Production настройки
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://casino_user:casino_password@localhost:5432/casino_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dazino Casino - Production", version="1.0.0")

# CORS для production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com", "https://www.your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Статические файлы
app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/music", StaticFiles(directory="music"), name="music")

# Импортируем все роуты из основного main.py
from main import (
    HealthResponse, SpinRequest, SpinResponse, RegisterRequest, RegisterResponse, 
    LoginRequest, PFRotationResponse, process_spin
)

# Health check
@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "production:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # В production reload отключен
        workers=4,   # Множество воркеров для производительности
    )
