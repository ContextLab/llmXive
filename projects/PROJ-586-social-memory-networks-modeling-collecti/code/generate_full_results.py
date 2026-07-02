from __future__ import annotations

from typing import Any, Tuple

from metrics.specialization import (
    SpecializationMetrics,
    compute_specialization_index,
)
from metrics.retrieval import RetrievalMetrics, compute_retrieval_efficiency

import numpy as np

def _deterministic_simulation(
    agent_count: int,
    context: str,
    game_id: int | None = None,
) -> Tuple[SpecializationMetrics, RetrievalMetrics]:
    """
    Very lightweight deterministic stand‑in for a full simulation.

    * ``specialization_index`` is defined as log₂(agent_count) (or 0 for 0 agents).
    * ``retrieval_efficiency`` is defined as 1 / agent_count (or 0 for 0 agents).
    """
    agent_count = max(0, int(agent_count))
    spec_index = compute_specialization_index(agent_count)
    # For retrieval we treat “correct” as 1 and “total” as agent_count,
    # yielding an efficiency of 1/agent_count.
    retrieval_metrics, _ = compute_retrieval_efficiency(
        correct=1,
        total=agent_count if agent_count > 0 else 1,
        num_agents=agent_count if agent_count > 0 else 1,
    )
    spec_metrics = SpecializationMetrics(specialization_index=spec_index)
    return spec_metrics, retrieval_metrics

def simulate_one_game(*args: Any, **kwargs: Any) -> Tuple[SpecializationMetrics, RetrievalMetrics]:
    """
    Compatibility wrapper that accepts the various calling conventions used
    throughout the code base.

    Supported signatures (all optional, extra keys ignored):
        - simulate_one_game(agent_count=..., context=..., game_id=...)
        - simulate_one_game(agents, context, game_id)
        - simulate_one_game(agent_count, context)

    The function forwards the extracted values to a deterministic simulation
    routine and returns the metric objects.
    """
    # Extract possible positional arguments
    if len(args) >= 2:
        agent_count = args[0]
        context = args[1]
        game_id = args[2] if len(args) > 2 else None
    else:
        agent_count = kwargs.get("agent_count") or kwargs.get("agents")
        context = kwargs.get("context")
        game_id = kwargs.get("game_id")

    # Fallback defaults
    agent_count = int(agent_count) if agent_count is not None else 0
    context = str(context) if context is not None else "full"

    return _deterministic_simulation(agent_count, context, game_id)
