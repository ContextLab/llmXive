"""Retrieval efficiency metrics.

Computes cue-retrieval efficiency for collective remembering experiments.
Measures how effectively agents retrieve relevant information from the shared
memory buffer given available cues.
"""
from __future__ import annotations

from dataclasses import dataclass
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


def validate_retrieval_efficiency(retrieved: int, total: int, agents: Any) -> bool:
    """Validate retrieval efficiency inputs."""
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

    Accepts multiple call patterns for flexibility across different callers:
    1. compute_retrieval_efficiency(retrieved, total, agents) - positional
    2. compute_retrieval_efficiency(retrieved=..., total=..., agents=...) - keyword
    3. compute_retrieval_efficiency(agent_count, game_id) - legacy (ignored, uses defaults)
    4. compute_retrieval_efficiency(cues_attempted, cues_successful, agents) - explicit cue counts

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

    # Handle positional arguments
    if len(args) >= 1:
        # Check if this might be the legacy (agent_count, game_id) pattern
        # by checking if second arg is int and first is small
        if len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], int):
            # Could be legacy pattern - treat as (retrieved=0, total=1) defaults
            # or as (cues_attempted, cues_successful) if values are reasonable
            if args[0] <= 100:  # Heuristic: agent counts are small
                cues_attempted = args[0]
                cues_successful = args[1]
            else:
                retrieved = args[0]
                total = args[1]
        else:
            retrieved = args[0]
    if len(args) >= 2:
        if cues_attempted is None:  # Not already set above
            total = args[1]
        else:
            # Already handled as cues_successful
            pass
    if len(args) >= 3:
        agents = args[2]

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

    # Normalize agents count
    agent_count = agents
    if isinstance(agents, list):
        agent_count = len(agents)

    # Validate
    if not validate_retrieval_efficiency(retrieved, total, agent_count):
        raise ValueError(f"Invalid retrieval inputs: retrieved={retrieved}, total={total}, agents={agent_count}")

    # Compute metrics
    retrieval_rate = retrieved / total if total > 0 else 0.0

    # Efficiency: penalize based on agent count (more agents = harder to retrieve)
    # This reflects the increased complexity of coordination in larger groups
    base_efficiency = retrieval_rate
    agent_penalty = 1.0 / (1.0 + 0.1 * agent_count)
    efficiency_score = base_efficiency * agent_penalty

    # Calculate false positives/negatives if we have both attempted and successful
    false_positives = 0
    false_negatives = 0
    if cues_attempted is not None and cues_successful is not None:
        # False positives: attempts that didn't yield relevant info (simplified model)
        false_positives = max(0, cues_attempted - cues_successful - retrieved)
        # False negatives: missed opportunities (simplified model)
        false_negatives = max(0, total - retrieved - cues_successful)

    metrics = RetrievalMetrics(
        retrieval_rate=retrieval_rate,
        efficiency_score=efficiency_score,
        avg_retrieval_time=0.0,  # Would be measured in real implementation
        cues_attempted=cues_attempted or retrieved,
        cues_successful=cues_successful or retrieved,
        false_positives=false_positives,
        false_negatives=false_negatives
    )

    return metrics, efficiency_score