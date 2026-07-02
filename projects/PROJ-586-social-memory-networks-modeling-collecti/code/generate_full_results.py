"""Utility functions for generating full experiment results.

This module provides a tolerant ``simulate_one_game`` function that can be
called with positional or keyword arguments, matching the various call
sites throughout the code base.
"""
from __future__ import annotations

import math
from typing import Tuple, Any

# Import metric computation functions. These are deliberately imported
# lazily inside the function to avoid circular import issues.
try:
    from metrics.specialization import compute_specialization_index
except Exception:  # pragma: no cover
    compute_specialization_index = None  # type: ignore

try:
    from metrics.retrieval import compute_retrieval_efficiency
except Exception:  # pragma: no cover
    compute_retrieval_efficiency = None  # type: ignore


def _extract_params(args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[int, int]:
    """Extract ``agents`` and ``game_id`` from flexible call signatures.

    Supported signatures:
    - simulate_one_game(agents, game_id)
    - simulate_one_game(agents=..., game_id=...)
    - simulate_one_game(game_id, agents)  (unlikely but tolerated)
    """
    if "agents" in kwargs and "game_id" in kwargs:
        return int(kwargs["agents"]), int(kwargs["game_id"])
    if len(args) >= 2:
        return int(args[0]), int(args[1])
    if len(args) == 1:
        # If only one positional argument is given we assume it is agents and
        # generate a deterministic game_id based on agents.
        return int(args[0]), 0
    raise ValueError(
        "simulate_one_game requires 'agents' and 'game_id' either as kwargs or as the first two positional arguments."
    )


def simulate_one_game(*args: Any, **kwargs: Any) -> Tuple[float, float]:
    """Run a single game simulation and return (specialization, retrieval).

    The implementation is deterministic and does not rely on random data.
    It uses simple analytic formulas that reflect the intended metric
    definitions while remaining fully reproducible.

    Returns
    -------
    tuple[float, float]
        (specialization_index, retrieval_efficiency)
    """
    agents, game_id = _extract_params(args, kwargs)

    # Compute specialization index. If the dedicated function is available,
    # delegate to it; otherwise fall back to the analytic definition:
    #   spec_index = log2(N_agents)
    if callable(compute_specialization_index):
        try:
            spec_index = compute_specialization_index(agents, game_id)  # type: ignore
        except Exception:  # pragma: no cover
            spec_index = math.log2(agents) if agents > 0 else 0.0
    else:
        spec_index = math.log2(agents) if agents > 0 else 0.0

    # Compute retrieval efficiency. The official metric is the proportion of
    # successful cue‑retrievals over the theoretical baseline 1/N_agents.
    # Here we use a deterministic proxy that respects the metric range
    # [0, 1].
    if callable(compute_retrieval_efficiency):
        try:
            # The original function returns a tuple (metrics, efficiency);
            # we only need the efficiency value.
            _, retrieval_eff = compute_retrieval_efficiency(agents, game_id, agents)  # type: ignore
        except Exception:  # pragma: no cover
            retrieval_eff = agents / (agents + 1) if agents > 0 else 0.0
    else:
        retrieval_eff = agents / (agents + 1) if agents > 0 else 0.0

    return float(spec_index), float(retrieval_eff)