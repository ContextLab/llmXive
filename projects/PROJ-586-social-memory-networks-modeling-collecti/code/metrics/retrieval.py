"""Retrieval efficiency metrics for social memory networks.

This module implements the cue-retrieval efficiency metric (FR-005) which
measures how effectively agents retrieve relevant information from the
shared memory buffer relative to the total available information.

The retrieval efficiency is calculated as:
    efficiency = (relevant_retrieved / total_relevant) * (1 - false_positive_rate)

Where:
    - relevant_retrieved: number of correctly retrieved items
    - total_relevant: total number of relevant items in memory
    - false_positive_rate: proportion of irrelevant items retrieved
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


@dataclass
class RetrievalMetrics:
    """Container for retrieval efficiency metrics."""

    game_id: int
    agent_count: int
    relevant_items: int
    retrieved_count: int
    relevant_retrieved: int
    irrelevant_retrieved: int
    efficiency: float
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    context_condition: str = "full"

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "game_id": self.game_id,
            "agent_count": self.agent_count,
            "relevant_items": self.relevant_items,
            "retrieved_count": self.retrieved_count,
            "relevant_retrieved": self.relevant_retrieved,
            "irrelevant_retrieved": self.irrelevant_retrieved,
            "efficiency": self.efficiency,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "false_positive_rate": self.false_positive_rate,
            "context_condition": self.context_condition,
        }


def validate_retrieval_efficiency(
    retrieved: Union[int, List[int]],
    total: Union[int, List[int]],
    agents: Union[int, List[int], None] = None,
) -> bool:
    """Validate inputs for retrieval efficiency computation.

    Args:
        retrieved: Number of items retrieved (can be per-agent list or total)
        total: Total relevant items available (can be per-agent list or total)
        agents: Number of agents (optional, inferred if not provided)

    Returns:
        True if inputs are valid, False otherwise.

    Raises:
        ValueError: If inputs are invalid (negative, inconsistent shapes).
    """
    # Handle list inputs
    if isinstance(retrieved, list) and isinstance(total, list):
        if len(retrieved) != len(total):
            raise ValueError("retrieved and total must have same length if both are lists")
        if agents is None:
            agents = len(retrieved)
    elif isinstance(retrieved, int) and isinstance(total, int):
        if agents is None:
            agents = 1
    else:
        raise ValueError("retrieved and total must both be int or both be list")

    # Validate non-negative
    if isinstance(retrieved, int):
        if retrieved < 0:
            raise ValueError("retrieved must be non-negative")
    else:
        if any(r < 0 for r in retrieved):
            raise ValueError("all retrieved values must be non-negative")

    if isinstance(total, int):
        if total < 0:
            raise ValueError("total must be non-negative")
    else:
        if any(t < 0 for t in total):
            raise ValueError("all total values must be non-negative")

    # Validate agents
    if isinstance(agents, int):
        if agents <= 0:
            raise ValueError("agents must be positive")
    elif isinstance(agents, list):
        if any(a <= 0 for a in agents):
            raise ValueError("all agent counts must be positive")
    else:
        raise ValueError("agents must be int or list of ints")

    return True


def compute_retrieval_efficiency(
    retrieved: Union[int, List[int], Any] = None,
    total: Union[int, List[int], Any] = None,
    agents: Union[int, List[int], Any] = None,
    relevant_retrieved: Optional[Union[int, List[int]]] = None,
    irrelevant_retrieved: Optional[Union[int, List[int]]] = None,
    game_id: Optional[int] = None,
    context_condition: str = "full",
    **kwargs: Any,
) -> Tuple[RetrievalMetrics, float]:
    """Compute retrieval efficiency metrics for a game or batch of games.

    This function implements the core retrieval efficiency metric (FR-005)
    with flexible input handling to support various call patterns:

    1. Full game result: provide relevant_retrieved, irrelevant_retrieved, total
    2. Simple counts: provide retrieved, total, agents
    3. Per-agent breakdown: provide lists for retrieved, total, agents

    Args:
        retrieved: Number of items retrieved (int or list)
        total: Total relevant items available (int or list)
        agents: Number of agents (int or list)
        relevant_retrieved: Explicit count of correctly retrieved items
        irrelevant_retrieved: Explicit count of incorrectly retrieved items
        game_id: Optional game identifier
        context_condition: Context condition label ("full" or "limited")
        **kwargs: Additional arguments for legacy compatibility

    Returns:
        Tuple of (RetrievalMetrics, efficiency_value)

    Raises:
        ValueError: If inputs are invalid or inconsistent.
    """
    # Handle legacy call patterns
    if retrieved is None and total is None and agents is None:
        # Check if we have explicit counts
        if relevant_retrieved is not None and irrelevant_retrieved is not None:
            retrieved = relevant_retrieved + irrelevant_retrieved
            total = kwargs.get("total_relevant", kwargs.get("total", 0))
            agents = kwargs.get("agent_count", kwargs.get("agents", 1))
        else:
            # Fallback: use kwargs for legacy patterns
            retrieved = kwargs.get("retrieved", 0)
            total = kwargs.get("total", 0)
            agents = kwargs.get("agents", kwargs.get("agent_count", 1))

    # Validate inputs
    validate_retrieval_efficiency(retrieved, total, agents)

    # Normalize to lists for uniform processing
    if isinstance(retrieved, int):
        retrieved = [retrieved]
    if isinstance(total, int):
        total = [total]
    if isinstance(agents, int):
        agents = [agents]

    # Ensure consistent lengths
    n = len(retrieved)
    if len(total) != n:
        total = total * n if isinstance(total, list) else [total[0] if total else 0] * n
    if len(agents) != n:
        agents = agents * n if isinstance(agents, list) else [agents[0] if agents else 1] * n

    # Compute per-game metrics
    efficiencies = []
    metrics_list = []

    for i in range(n):
        r = retrieved[i] if i < len(retrieved) else 0
        t = total[i] if i < len(total) else 0
        a = agents[i] if i < len(agents) else 1

        # Handle explicit counts if provided
        if relevant_retrieved is not None:
            rr = relevant_retrieved[i] if isinstance(relevant_retrieved, list) else relevant_retrieved
            ir = irrelevant_retrieved[i] if isinstance(irrelevant_retrieved, list) else irrelevant_retrieved
        else:
            # Infer from retrieved and total
            rr = min(r, t) if t > 0 else 0
            ir = max(0, r - t)

        # Calculate precision, recall, and efficiency
        precision = rr / r if r > 0 else 0.0
        recall = rr / t if t > 0 else 0.0
        fpr = ir / (r - rr) if (r - rr) > 0 else 0.0

        # Efficiency combines recall and penalizes false positives
        # efficiency = recall * (1 - fpr)
        efficiency = recall * (1 - fpr) if t > 0 else 0.0

        efficiencies.append(efficiency)

        # Create metrics object
        game_id_i = (game_id + i) if game_id is not None else i
        metrics = RetrievalMetrics(
            game_id=game_id_i,
            agent_count=a,
            relevant_items=t,
            retrieved_count=r,
            relevant_retrieved=rr,
            irrelevant_retrieved=ir,
            efficiency=efficiency,
            precision=precision,
            recall=recall,
            f1_score=2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0,
            false_positive_rate=fpr,
            context_condition=context_condition,
        )
        metrics_list.append(metrics)

    # Return single metrics if only one game, else list
    if len(metrics_list) == 1:
        return metrics_list[0], efficiencies[0]

    # For batch, return aggregated metrics
    avg_efficiency = float(np.mean(efficiencies))
    return metrics_list, avg_efficiency


def batch_compute_retrieval_efficiency(
    game_results: List[Dict[str, Any]],
    context_condition: str = "full",
) -> Tuple[List[RetrievalMetrics], float]:
    """Compute retrieval efficiency for a batch of game results.

    Args:
        game_results: List of game result dictionaries containing retrieval data
        context_condition: Context condition label

    Returns:
        Tuple of (list of RetrievalMetrics, average efficiency)

    Raises:
        ValueError: If game_results is empty or contains invalid data.
    """
    if not game_results:
        raise ValueError("game_results cannot be empty")

    metrics_list = []
    efficiencies = []

    for idx, result in enumerate(game_results):
        game_id = result.get("game_id", idx)
        agent_count = result.get("agent_count", 1)
        total_relevant = result.get("total_relevant", 0)
        retrieved_count = result.get("retrieved_count", 0)
        relevant_retrieved = result.get("relevant_retrieved", 0)
        irrelevant_retrieved = result.get("irrelevant_retrieved", 0)

        # Compute metrics for this game
        metrics, efficiency = compute_retrieval_efficiency(
            retrieved=retrieved_count,
            total=total_relevant,
            agents=agent_count,
            relevant_retrieved=relevant_retrieved,
            irrelevant_retrieved=irrelevant_retrieved,
            game_id=game_id,
            context_condition=context_condition,
        )

        metrics_list.append(metrics)
        efficiencies.append(efficiency)

    avg_efficiency = float(np.mean(efficiencies)) if efficiencies else 0.0
    return metrics_list, avg_efficiency