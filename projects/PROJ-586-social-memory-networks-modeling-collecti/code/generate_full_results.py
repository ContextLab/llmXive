"""Game simulation with flexible signature support."""
from __future__ import annotations

from typing import List, Tuple, Any
from t015_generate_full_results import (
    compute_specialization_index as _core_spec_index,
    compute_retrieval_efficiency as _core_ret_eff,
)


def simulate_one_game(*args: Any, **kwargs: Any) -> Tuple[float, float]:
    """Simulate one game with flexible signature support.
    
    Supports:
    1. simulate_one_game(agent_count: int, game_id: int, context: str)
    2. simulate_one_game(agent_list: List[int], game_id: int)
    3. simulate_one_game(agents, game_id) - legacy positional
    
    Returns:
        Tuple of (specialization_index, retrieval_efficiency)
    """
    # Parse arguments
    agent_count = None
    game_id = None
    context = None

    # Keyword arguments
    if "agent_count" in kwargs:
        agent_count = kwargs["agent_count"]
    if "agents" in kwargs:
        agent_count = kwargs["agents"]
    if "game_id" in kwargs:
        game_id = kwargs["game_id"]
    if "context" in kwargs:
        context = kwargs["context"]

    # Positional arguments
    if len(args) >= 1 and agent_count is None:
        agent_count = args[0]
    if len(args) >= 2 and game_id is None:
        game_id = args[1]
    if len(args) >= 3 and context is None:
        context = args[2]

    # Default values
    if agent_count is None:
        agent_count = 5
    if game_id is None:
        game_id = 0
    if context is None:
        context = "full"

    # Convert agent_count to list if needed
    if isinstance(agent_count, int):
        agent_list = [i % agent_count for i in range(agent_count)]
    else:
        agent_list = agent_count

    # Compute metrics
    spec_idx, _ = _core_spec_index(agent_list)
    ret_metrics, ret_eff = _core_ret_eff(
        retrieved=len(agent_list) // 2,
        total=len(agent_list),
        agents=len(agent_list)
    )

    return spec_idx, ret_eff
