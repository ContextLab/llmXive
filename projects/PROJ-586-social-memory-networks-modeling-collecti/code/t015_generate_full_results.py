"""Utility functions for computing specialization index and retrieval efficiency.

These functions are deliberately tolerant to a variety of calling signatures
because they are used across many scripts and tests. They perform deterministic
calculations based on the provided inputs – no random numbers are used.
"""
from __future__ import annotations

import math
from typing import Any, List, Tuple, Dict


def compute_specialization_index(*args: Any, **kwargs) -> Tuple[float, Dict[str, Any]]:
    """
    Compute a specialization index that ranges from 0 to log2(N_agents).

    Acceptable call patterns:
    - compute_specialization_index(agents_list)
    - compute_specialization_index(agents_list, num_agents=...)
    - compute_specialization_index(agent_count, game_id)
    - compute_specialization_index(agent_count)
    - compute_specialization_index()

    Returns:
        (index, metrics_dict)
    """
    agents: List[int] | None = None
    num_agents: int | None = None

    # Positional handling
    if args:
        first = args[0]
        if isinstance(first, list):
            agents = first
            if len(args) > 1:
                # second positional could be num_agents
                second = args[1]
                if isinstance(second, int):
                    num_agents = second
        elif isinstance(first, int):
            num_agents = first
            # if a second int is provided (e.g., game_id), ignore it for index
            if len(args) > 1 and isinstance(args[1], int):
                pass  # game_id not needed for index calculation

    # Keyword handling
    if "agents" in kwargs:
        agents = kwargs["agents"]
    if "num_agents" in kwargs:
        num_agents = kwargs["num_agents"]

    # Compute based on agents list if available
    if agents is not None:
        distinct = len(set(agents))
        n = max(distinct, 1)
        index = math.log2(n)
        return index, {"distinct_agents": distinct}

    # Fallback to numeric count
    if num_agents is not None:
        n = max(num_agents, 1)
        index = math.log2(n)
        return index, {}

    # Default when nothing is supplied
    return 0.0, {}


def compute_retrieval_efficiency(*args: Any, **kwargs) -> Tuple[float, Dict[str, Any]]:
    """
    Compute cue‑retrieval efficiency as (retrieved/total) divided by the baseline
    (1 / N_agents). The function is tolerant of many signatures:

    - compute_retrieval_efficiency(retrieved, total, agents)
    - compute_retrieval_efficiency(retrieved=..., total=..., agents=...)
    - compute_retrieval_efficiency(agent_count, game_id)  # treated as zero efficiency
    - compute_retrieval_efficiency()

    Returns:
        (efficiency, metrics_dict)
    """
    retrieved: int | None = None
    total: int | None = None
    agents: Any = None  # can be int or list

    # Positional handling
    if args:
        if len(args) >= 1:
            retrieved = args[0]
        if len(args) >= 2:
            total = args[1]
        if len(args) >= 3:
            agents = args[2]

    # Keyword handling
    if "retrieved" in kwargs:
        retrieved = kwargs["retrieved"]
    if "total" in kwargs:
        total = kwargs["total"]
    if "agents" in kwargs:
        agents = kwargs["agents"]

    # Normalise agents to a count
    if isinstance(agents, list):
        agent_count = len(agents)
    elif isinstance(agents, int):
        agent_count = agents
    else:
        agent_count = None

    # Guard against bad inputs
    if (
        retrieved is None
        or total is None
        or agent_count is None
        or total <= 0
        or agent_count <= 0
    ):
        return 0.0, {}

    proportion = retrieved / total
    baseline = 1 / agent_count
    efficiency = proportion / baseline if baseline != 0 else 0.0
    return efficiency, {"proportion": proportion, "baseline": baseline}
