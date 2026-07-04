"""Wrapper for simulate_one_game from t015."""
from __future__ import annotations

from typing import List, Tuple, Any
from t015_generate_full_results import simulate_one_game as _simulate_one_game


def simulate_one_game(
    agent_count_or_list: Any,
    game_id: int = 0,
    context: str = "full"
) -> Tuple[float, float]:
    """Wrapper for simulate_one_game that delegates to t015."""
    return _simulate_one_game(agent_count_or_list, game_id, context)
