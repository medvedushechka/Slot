from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from models import ReelWeights
from slot_engine import DEFAULT_REELS_MATRIX, ReelMatrix


RedisLike = Any


def get_reels_matrix_for_bet(
    db: Session, bet: float, redis_client: Optional[RedisLike] = None
) -> ReelMatrix:
    """Возвращает матрицу барабанов для заданной ставки.

    Порядок приоритета:
    1) Точный матч по bet_amount
    2) Наибольший bet_amount <= bet
    3) Наименьший bet_amount > bet
    4) DEFAULT_REELS_MATRIX
    """

    cache_key = f"reels:bet:{bet}"
    if redis_client is not None:
        try:
            cached = redis_client.get(cache_key)
        except Exception:
            cached = None
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                pass

    query = db.query(ReelWeights)

    reel_row = (
        query.filter(ReelWeights.bet_amount == bet).first()
        or query.filter(ReelWeights.bet_amount <= bet)
        .order_by(ReelWeights.bet_amount.desc())
        .first()
        or query.filter(ReelWeights.bet_amount > bet)
        .order_by(ReelWeights.bet_amount.asc())
        .first()
    )

    if reel_row is not None and reel_row.reels:
        matrix = reel_row.reels
        if redis_client is not None:
            try:
                redis_client.setex(cache_key, 60, json.dumps(matrix))
            except Exception:
                pass
        return matrix

    return DEFAULT_REELS_MATRIX


def acquire_spin_lock(
    redis_client: Optional[RedisLike], user_id: int, ttl_seconds: int = 5
) -> bool:
    """Пытается поставить лок на спин пользователя.

    Если Redis не доступен — всегда возвращает True (без локов, но слот работает).
    """

    if redis_client is None:
        return True

    key = f"lock:spin:{user_id}"
    try:
        # NX=true — только если ключа ещё нет, EX=ttl_seconds — авто-истечение
        return bool(redis_client.set(key, "1", nx=True, ex=ttl_seconds))
    except Exception:
        return True


def release_spin_lock(redis_client: Optional[RedisLike], user_id: int) -> None:
    if redis_client is None:
        return

    key = f"lock:spin:{user_id}"
    try:
        redis_client.delete(key)
    except Exception:
        pass
