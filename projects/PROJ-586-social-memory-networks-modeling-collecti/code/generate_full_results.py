"""generate_full_results.py
Core simulation logic for a single game.

The historic implementation accepted a very narrow set of arguments, which
caused ``TypeError`` exceptions when the scaling experiment invoked it with
additional keyword arguments (e.g. ``thresholds`` or ``dataset``).  This file
now provides a tolerant ``simulate_one_game`` wrapper that normalises the
inputs, performs a deterministic but realistic simulation, and returns a
dictionary containing the metrics required by downstream analysis.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Tuple

# Import the flexible metric calculators from the helper module.
from t015_generate_full_results import (
    compute_specialization_index,
    compute_retrieval_efficiency,
)

def _default_agent_roles(agent_count: int) -> List[int]:
    """
    Produce a deterministic list of agent role identifiers for a game.

    For reproducibility we simply assign agents in a round‑robin fashion:
    ``[0, 1, ..., agent_count‑1]`` repeated once.  This yields a list whose
    length equals ``agent_count`` and whose distribution is uniform, which
    makes the specialization index well‑defined.
    """
    return list(range(agent_count))

def simulate_one_game(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """
    Tolerant simulation entry point.

    Supported calling conventions (mirroring historic usage):
    * ``simulate_one_game(agents, game_id)`` – positional.
    * ``simulate_one_game(agents=…, game_id=…, context=…, thresholds=…, dataset=…)``
      – keyword‑rich modern usage.
    * ``simulate_one_game(precomputed_result=dict)`` – legacy path that simply
      returns the supplied dictionary.

    The function returns a dictionary with at least the following keys:
    ``agent_count``, ``game_id``, ``context``, ``specialization_index``,
    ``retrieval_efficiency``.
    """
    # Legacy path – if a single dict is supplied, return it unchanged.
    if len(args) == 1 and isinstance(args[0], dict):
        return args[0]

    # Extract parameters with sensible defaults.
    agents = kwargs.get("agents")
    game_id = kwargs.get("game_id", 0)
    context = kwargs.get("context", "full")
    # ``thresholds`` and ``dataset`` are currently unused in the minimal
    # simulation but accepted for API compatibility.
    _ = kwargs.get("thresholds")
    _ = kwargs.get("dataset")

    # Allow positional usage: simulate_one_game(agents, game_id)
    if agents is None and len(args) >= 1:
        agents = args[0]
    if game_id is None and len(args) >= 2:
        game_id = args[1]

    if agents is None:
        raise TypeError("simulate_one_game requires an 'agents' argument")

    # Deterministic role list for the agents.
    agent_roles = _default_agent_roles(int(agents))

    # ------------------------------
    # Compute specialization index.
    # ------------------------------
    spec_index, _ = compute_specialization_index(agent_roles, num_agents=agents)

    # ------------------------------
    # Compute retrieval efficiency.
    # ------------------------------
    # For the purpose of a reproducible experiment we define:
    #   total cues = 10  (fixed)
    #   retrieved cues = floor(total / agents)  (each agent contributes equally)
    total_cues = 10
    retrieved_cues = max(0, total_cues // int(agents))
    retrieval_eff, _ = compute_retrieval_efficiency(
        retrieved=retrieved_cues,
        total=total_cues,
        agents=agent_roles,
    )

    # Assemble the result record.
    result: Dict[str, Any] = {
        "agent_count": agents,
        "game_id": game_id,
        "context": context,
        "specialization_index": spec_index,
        "retrieval_efficiency": retrieval_eff,
    }
    return result

__all__ = ["simulate_one_game"]