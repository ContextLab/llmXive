"""Wrapper module that re-exports from t015_generate_full_results."""
from __future__ import annotations
from typing import List, Tuple, Any
from t015_generate_full_results import (
    GameResult,
    compute_specialization_index,
    compute_retrieval_efficiency,
    simulate_one_game as _simulate_one_game,
    run_simulation,
    write_results_csv,
)

__all__ = [
    "GameResult",
    "compute_specialization_index",
    "compute_retrieval_efficiency",
    "simulate_one_game",
    "run_simulation",
    "write_results_csv",
]


def simulate_one_game(
    agent_count: Any = None,
    game_id: Any = None,
    context: Any = None,
    **kwargs: Any,
) -> GameResult:
    """Wrapper that delegates to t015_generate_full_results.simulate_one_game."""
    return _simulate_one_game(
        agent_count=agent_count,
        game_id=game_id,
        context=context,
        **kwargs,
    )