import random
from typing import List, Dict, Any, Optional
import hashlib


Symbol = str
ReelCell = Dict[str, Any]
ReelMatrix = List[List[ReelCell]]


SYMBOL_PAYOUTS: Dict[str, float] = {
    "A": 2.0,
    "K": 3.0,
    "Q": 5.0,
    "WILD": 10.0,
}


DEFAULT_REELS_MATRIX: ReelMatrix = [
    [
        {"symbol": "A", "weight": 40},
        {"symbol": "K", "weight": 30},
        {"symbol": "Q", "weight": 20},
        {"symbol": "WILD", "weight": 10},
    ],
    [
        {"symbol": "A", "weight": 40},
        {"symbol": "K", "weight": 30},
        {"symbol": "Q", "weight": 20},
        {"symbol": "WILD", "weight": 10},
    ],
    [
        {"symbol": "A", "weight": 40},
        {"symbol": "K", "weight": 30},
        {"symbol": "Q", "weight": 20},
        {"symbol": "WILD", "weight": 10},
    ],
]

def provably_fair_spin_reels(
    reels_matrix: Optional[ReelMatrix],
    server_seed: str,
    client_seed: str,
    nonce: int,
) -> List[Symbol]:
    matrix = reels_matrix or DEFAULT_REELS_MATRIX
    result: List[Symbol] = []

    for reel_index, reel in enumerate(matrix):
        total_weight = sum(int(cell["weight"]) for cell in reel)
        if total_weight <= 0:
            total_weight = len(reel)
            uniform = True
        else:
            uniform = False

        seed_input = f"{server_seed}:{client_seed}:{nonce}:{reel_index}"
        digest = hashlib.sha256(seed_input.encode("utf-8")).digest()
        rnd_int = int.from_bytes(digest[:8], byteorder="big")

        if uniform:
            index = rnd_int % len(reel)
            chosen_symbol = reel[index]["symbol"]
        else:
            target = rnd_int % total_weight
            cumulative = 0
            chosen_symbol = reel[-1]["symbol"]
            for cell in reel:
                cumulative += int(cell["weight"])
                if target < cumulative:
                    chosen_symbol = cell["symbol"]
                    break

        result.append(chosen_symbol)

    return result


def spin_reels(reels_matrix: Optional[ReelMatrix] = None) -> List[Symbol]:
    """Крутит барабаны и возвращает выпавший символ на каждом барабане."""
    matrix = reels_matrix or DEFAULT_REELS_MATRIX
    result: List[Symbol] = []

    for reel in matrix:
        symbols = [cell["symbol"] for cell in reel]
        weights = [cell["weight"] for cell in reel]
        chosen_symbol = random.choices(symbols, weights=weights, k=1)[0]
        result.append(chosen_symbol)

    return result


def calculate_win(result: List[Symbol], bet: float) -> float:
    """Очень простой расчёт: 3 одинаковых символа по линии = bet * множитель."""
    if bet <= 0:
        return 0.0

    if len(result) != 3:
        return 0.0

    s1, s2, s3 = result
    if s1 == s2 == s3:
        multiplier = SYMBOL_PAYOUTS.get(s1, 0.0)
        return bet * multiplier

    return 0.0


def spin_and_calculate(bet: float, reels_matrix: Optional[ReelMatrix] = None) -> Dict[str, Any]:
    """Удобная обёртка: крутит барабаны и считает выигрыш."""
    symbols = spin_reels(reels_matrix=reels_matrix)
    win = calculate_win(symbols, bet)
    return {
        "symbols": symbols,
        "win": win,
    }
