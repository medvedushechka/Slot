from sqlalchemy import Column, Integer, Float, String, JSON, DateTime
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Spin(Base):
    __tablename__ = "spins"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    bet = Column(Float)
    win = Column(Float)
    symbols = Column(String)  # JSON строка с исходами
    pf_data = Column(JSON, nullable=True)

class BonusMeter(Base):
    __tablename__ = "bonus_meters"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    small_win_meter = Column(Integer, default=0)
    bet_total_meter = Column(Float, default=0.0)
    time_meter = Column(Integer, default=0)  # В минутах

class SessionData(Base):
    __tablename__ = "session_data"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    spin_count = Column(Integer, default=0)
    loss_streak = Column(Integer, default=0)
    current_rtp = Column(Float, default=0.0)
    total_bets = Column(Float, default=0.0)
    total_wins = Column(Float, default=0.0)

class ReelWeights(Base):
    __tablename__ = "reel_weights"
    id = Column(Integer, primary_key=True)
    bet_amount = Column(Float)
    reels = Column(JSON)  # Динамические веса

class ProvablyFairState(Base):
    __tablename__ = "provably_fair_state"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, index=True)
    server_seed = Column(String)
    server_seed_hash = Column(String)
    nonce = Column(Integer, default=0)