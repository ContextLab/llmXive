"""Retrieval efficiency metrics.

Computes cue-retrieval efficiency for collective remembering experiments.
Measures how effectively agents retrieve relevant information from the shared
memory buffer given available cues.

This module implements the metric described in FR-005: "Cue-retrieval efficiency
is the ratio of successfully retrieved relevant items to total available cues,
adjusted for false positives and agent count."
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Any, List, Optional


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval efficiency."""
    retrieval_rate: float
    efficiency_score: float
    avg_retrieval_time: float = 0.0
    cues_attempted: int = 0
    cues_successful: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    total_cues_available: int = 0
    relevant_items_retrieved: int = 0


def validate_retrieval_efficiency(retrieved: int, total: int, agents: Any) -> bool:
    """Validate retrieval efficiency inputs.

    Args:
        retrieved: Number of items successfully retrieved
        total: Total number of items/cues available
        agents: Agent count or list of agents

    Returns:
        True if inputs are valid, False otherwise
    """
    if not isinstance(retrieved, int) or retrieved < 0:
        return False
    if not isinstance(total, int) or total < 0:
        return False
    if retrieved > total:
        return False
    if isinstance(agents, int) and agents <= 0:
        return False
    if isinstance(agents, list) and len(agents) == 0:
        return False
    return True


def compute_retrieval_efficiency(*args: Any, **kwargs: Any) -> Tuple[RetrievalMetrics, float]:
    """Compute retrieval efficiency metric.

    This function accepts multiple call patterns to support different callers
    across the codebase:

    1. compute_retrieval_efficiency(retrieved, total, agents) - positional
    2. compute_retrieval_efficiency(retrieved=..., total=..., agents=...) - keyword
    3. compute_retrieval_efficiency(agent_count, game_id) - legacy (ignored)
    4. compute_retrieval_efficiency(cues_attempted, cues_successful, agents) - explicit cue counts
    5. compute_retrieval_efficiency(retrieved, total, agents, relevant_items) - with relevant items
    6. compute_retrieval_efficiency(game_results, agents) - from game results list

    Args:
        *args: Positional arguments (retrieved, total, agents) or (agent_count, game_id)
        **kwargs: Keyword arguments for any of the above parameters

    Returns:
        Tuple of (RetrievalMetrics, efficiency_score)

    Raises:
        ValueError: If inputs are invalid
    """
    retrieved = None
    total = None
    agents = None
    cues_attempted = None
    cues_successful = None
    relevant_items = None
    game_results = None

    # Handle positional arguments
    if len(args) >= 1:
        # Check if this might be the legacy (agent_count, game_id) pattern
        if len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], int):
            # Could be legacy pattern - treat as defaults
            if args[0] <= 100:  # Heuristic: agent counts are small
                cues_attempted = args[0]
                cues_successful = args[1]
            else:
                retrieved = args[0]
                total = args[1]
        else:
            retrieved = args[0]
    if len(args) >= 2:
        if cues_attempted is None:
            total = args[1]
    if len(args) >= 3:
        agents = args[2]
    if len(args) >= 4:
        relevant_items = args[3]

    # Handle keyword arguments (override positional)
    if 'retrieved' in kwargs:
        retrieved = kwargs['retrieved']
    if 'total' in kwargs:
        total = kwargs['total']
    if 'agents' in kwargs:
        agents = kwargs['agents']
    if 'cues_attempted' in kwargs:
        cues_attempted = kwargs['cues_attempted']
    if 'cues_successful' in kwargs:
        cues_successful = kwargs['cues_successful']
    if 'relevant_items' in kwargs:
        relevant_items = kwargs['relevant_items']
    if 'game_results' in kwargs:
        game_results = kwargs['game_results']

    # Handle game_results list input
    if game_results is not None:
        if isinstance(game_results, list) and len(game_results) > 0:
            # Extract retrieval data from game results
            total_retrieved = 0
            total_cues = 0
            total_relevant = 0
            
            for result in game_results:
                if isinstance(result, dict):
                    total_retrieved += result.get('retrieved', 0)
                    total_cues += result.get('total_cues', result.get('total', 0))
                    total_relevant += result.get('relevant_items', result.get('total', 0))
                elif hasattr(result, 'retrieved'):
                    total_retrieved += getattr(result, 'retrieved', 0)
                    total_cues += getattr(result, 'total_cues', getattr(result, 'total', 0))
                    total_relevant += getattr(result, 'relevant_items', getattr(result, 'total', 0))
            
            retrieved = total_retrieved
            total = total_cues
            relevant_items = total_relevant
            if agents is None:
                agents = len(game_results)

    # Resolve from cues if provided
    if cues_attempted is not None and cues_successful is not None:
        retrieved = cues_successful
        total = cues_attempted

    # Default values if not provided
    if retrieved is None:
        retrieved = 0
    if total is None:
        total = 1
    if agents is None:
        agents = 3
    if relevant_items is None:
        relevant_items = total

    # Normalize agents count
    agent_count = agents
    if isinstance(agents, list):
        agent_count = len(agents)

    # Validate
    if not validate_retrieval_efficiency(retrieved, total, agent_count):
        raise ValueError(
            f"Invalid retrieval inputs: retrieved={retrieved}, total={total}, agents={agent_count}"
        )

    # Compute metrics
    retrieval_rate = retrieved / total if total > 0 else 0.0

    # Efficiency calculation per FR-005:
    # Base efficiency is retrieval rate, adjusted for:
    # 1. Agent count (coordination complexity increases with group size)
    # 2. False positive penalty (retrieving irrelevant items)
    # 3. False negative penalty (missing relevant items)
    
    base_efficiency = retrieval_rate
    
    # Agent penalty: more agents = harder coordination
    # Formula: 1 / (1 + 0.1 * n) where n is agent count
    agent_penalty = 1.0 / (1.0 + 0.1 * agent_count)
    
    # False positive penalty: penalize for retrieving irrelevant items
    # Simplified: assume false_positives = retrieved - relevant_items (if positive)
    false_positives = max(0, retrieved - relevant_items)
    fp_penalty = 1.0 - (0.1 * false_positives / max(1, retrieved))
    
    # False negative penalty: penalize for missing relevant items
    false_negatives = max(0, relevant_items - retrieved)
    fn_penalty = 1.0 - (0.1 * false_negatives / max(1, relevant_items))
    
    # Combined efficiency score
    efficiency_score = base_efficiency * agent_penalty * fp_penalty * fn_penalty
    
    # Ensure efficiency is in [0, 1]
    efficiency_score = max(0.0, min(1.0, efficiency_score))

    metrics = RetrievalMetrics(
        retrieval_rate=retrieval_rate,
        efficiency_score=efficiency_score,
        avg_retrieval_time=0.0,  # Would be measured in real implementation
        cues_attempted=cues_attempted or total,
        cues_successful=cues_successful or retrieved,
        false_positives=false_positives,
        false_negatives=false_negatives,
        total_cues_available=total,
        relevant_items_retrieved=retrieved
    )

    return metrics, efficiency_score


def batch_compute_retrieval_efficiency(
    retrieved_list: List[int],
    total_list: List[int],
    agent_counts: List[int]
) -> Tuple[List[RetrievalMetrics], List[float]]:
    """Compute retrieval efficiency for multiple games in batch.

    Args:
        retrieved_list: List of retrieved counts per game
        total_list: List of total cues per game
        agent_counts: List of agent counts per game

    Returns:
        Tuple of (list of RetrievalMetrics, list of efficiency scores)
    """
    if len(retrieved_list) != len(total_list) or len(retrieved_list) != len(agent_counts):
        raise ValueError("All input lists must have the same length")

    metrics_list = []
    efficiency_list = []

    for retrieved, total, agents in zip(retrieved_list, total_list, agent_counts):
        metrics, efficiency = compute_retrieval_efficiency(retrieved, total, agents)
        metrics_list.append(metrics)
        efficiency_list.append(efficiency)

    return metrics_list, efficiency_list