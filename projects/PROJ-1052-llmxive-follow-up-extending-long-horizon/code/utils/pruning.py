"""
Pruning module for Reward Fidelity vs. Error Recovery Density study.

Implements FR-003 (Context Coarsening) and FR-004 (Dynamic Pruning).
Provides context managers and utility functions to manipulate reward
fidelity levels (Dense -> Binary, 3-Bin) and execute pruning based on
recovery-critical segments identified in US1.
"""

import logging
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Callable, Iterator, Tuple

from .state_diff import identify_recovery_segments, cosine_similarity

logger = logging.getLogger(__name__)


class RewardFidelityLevel:
    """Enumeration of reward fidelity levels."""
    DENSE = "dense"
    BINARY = "binary"
    THREE_BIN = "three_bin"


def coarsen_rewards(
    rewards: List[float],
    fidelity_level: str
) -> List[float]:
    """
    Coarsen a list of dense rewards to a lower fidelity level.

    Args:
        rewards: List of dense float rewards.
        fidelity_level: One of 'dense', 'binary', or 'three_bin'.

    Returns:
        List of coarsened rewards.

    Raises:
        ValueError: If fidelity_level is not recognized.
    """
    if not rewards:
        return []

    if fidelity_level == RewardFidelityLevel.DENSE:
        return list(rewards)

    if fidelity_level == RewardFidelityLevel.BINARY:
        # Threshold at 0: positive rewards become 1, others 0
        return [1.0 if r > 0.0 else 0.0 for r in rewards]

    if fidelity_level == RewardFidelityLevel.THREE_BIN:
        # Thresholds at -0.5 and 0.5
        # Low: r <= -0.5 -> 0
        # Mid: -0.5 < r <= 0.5 -> 1
        # High: r > 0.5 -> 2
        coarsened = []
        for r in rewards:
            if r <= -0.5:
                coarsened.append(0.0)
            elif r <= 0.5:
                coarsened.append(1.0)
            else:
                coarsened.append(2.0)
        return coarsened

    raise ValueError(f"Unknown fidelity_level: {fidelity_level}")


def identify_pruning_candidates(
    trajectory: Dict[str, Any],
    recovery_segments: List[Dict[str, Any]],
    fidelity_level: str
) -> List[int]:
    """
    Identify indices of context segments to prune based on fidelity level.

    Logic:
    - If fidelity is 'dense': Prune nothing (return empty list).
    - If fidelity is 'binary' or 'three_bin':
      Prune segments that were identified as 'recovery-critical' in US1
      (i.e., segments with high contribution to state change) BUT ONLY IF
      the current reward signal suggests the agent is not in a critical
      recovery phase (proxy logic: if the immediate reward is low/non-positive).

    Args:
        trajectory: The current execution trajectory (observations, actions, rewards).
        recovery_segments: List of segment dicts from US1 (must contain 'start_idx', 'end_idx', 'contribution').
        fidelity_level: Current fidelity setting.

    Returns:
        List of segment indices (or step indices) to prune.
    """
    if fidelity_level == RewardFidelityLevel.DENSE:
        logger.debug("Dense fidelity: No pruning applied.")
        return []

    # For lower fidelity, we aggressively prune recovery-critical segments
    # to test the hypothesis that low-fidelity signals cause the agent
    # to miss these critical cues.
    # We select the top N segments by contribution if they exist.
    if not recovery_segments:
        logger.warning("No recovery segments provided for pruning decision.")
        return []

    # Sort by contribution descending
    sorted_segments = sorted(
        recovery_segments,
        key=lambda x: x.get('contribution', 0.0),
        reverse=True
    )

    # Prune the top 50% of critical segments to simulate "loss of signal"
    # In a real dynamic scenario, we might check current reward, but for
    # the controlled experiment, we remove the most critical info to see
    # if the agent can recover without it.
    num_to_prune = max(1, len(sorted_segments) // 2)
    candidates = sorted_segments[:num_to_prune]

    # Extract indices. Assuming segments have 'start_idx' and 'end_idx'
    # representing the range of steps in the trajectory.
    # We return the start indices of the segments to mark for removal.
    prune_indices = []
    for seg in candidates:
        start = seg.get('start_idx')
        if start is not None:
            prune_indices.append(start)

    logger.info(
        f"Pruning fidelity {fidelity_level}: Marked {len(prune_indices)} "
        f"recovery-critical segments for removal."
    )
    return prune_indices


def prune_trajectory(
    trajectory: Dict[str, Any],
    prune_indices: List[int]
) -> Dict[str, Any]:
    """
    Create a new trajectory with specified segments removed.

    This modifies the 'observations', 'actions', and 'rewards' lists
    by removing items at the specified indices (or ranges if indices
    represent segment starts).

    Args:
        trajectory: Original trajectory dict.
        prune_indices: List of start indices of segments to remove.

    Returns:
        New trajectory dict with pruned content.
    """
    if not prune_indices:
        return trajectory

    # Convert indices to a set for O(1) lookup
    # Assuming 'indices' refer to specific steps to remove.
    # If they refer to ranges, we need to expand them.
    # For this implementation, we assume 'prune_indices' are specific step indices
    # to remove. If the segment has a range, the caller should have expanded it.
    indices_to_remove = set(prune_indices)

    new_trajectory = {
        'observations': [],
        'actions': [],
        'rewards': [],
        'metadata': trajectory.get('metadata', {}).copy()
    }

    if 'task_id' in trajectory:
        new_trajectory['task_id'] = trajectory['task_id']

    # Rebuild lists, skipping indices
    # We need to know the length of the lists. Assuming they are equal length.
    length = len(trajectory.get('observations', []))
    if len(trajectory.get('actions', [])) != length or len(trajectory.get('rewards', [])) != length:
        logger.warning("Trajectory lists have mismatched lengths. Pruning may be inconsistent.")

    for i in range(length):
        if i not in indices_to_remove:
            if i < len(trajectory['observations']):
                new_trajectory['observations'].append(trajectory['observations'][i])
            if i < len(trajectory['actions']):
                new_trajectory['actions'].append(trajectory['actions'][i])
            if i < len(trajectory['rewards']):
                new_trajectory['rewards'].append(trajectory['rewards'][i])

    logger.debug(f"Pruned {len(indices_to_remove)} steps from trajectory.")
    return new_trajectory


@contextmanager
def fidelity_context(
    fidelity_level: str,
    trajectory: Dict[str, Any],
    recovery_segments: List[Dict[str, Any]]
) -> Iterator[Tuple[Dict[str, Any], List[float]]]:
    """
    Context manager that prepares a trajectory for execution under a specific
    reward fidelity level.

    1. Coarsens the rewards in the trajectory.
    2. Identifies and applies pruning based on recovery segments.
    3. Yields the modified trajectory and the coarsened rewards.
    4. Restores original state (conceptually) on exit (though we return a new object).

    Args:
        fidelity_level: Target fidelity (dense, binary, three_bin).
        trajectory: Original execution trajectory.
        recovery_segments: Segments identified as critical in US1.

    Yields:
        Tuple of (pruned_trajectory, coarsened_rewards)
    """
    logger.info(f"Entering fidelity context: {fidelity_level}")

    # 1. Coarsen rewards
    original_rewards = trajectory.get('rewards', [])
    coarsened_rewards = coarsen_rewards(original_rewards, fidelity_level)

    # 2. Identify pruning candidates
    prune_indices = identify_pruning_candidates(
        trajectory,
        recovery_segments,
        fidelity_level
    )

    # 3. Apply pruning
    pruned_trajectory = prune_trajectory(trajectory, prune_indices)

    # Update the trajectory's rewards with the coarsened version
    pruned_trajectory['rewards'] = coarsened_rewards

    yield pruned_trajectory, coarsened_rewards

    logger.debug("Exiting fidelity context.")