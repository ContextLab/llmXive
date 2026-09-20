import logging
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Callable, Iterator, Tuple, Union
from enum import Enum

import numpy as np
import pandas as pd

# Import from sibling module as per API surface
from .state_diff import identify_recovery_segments, cosine_similarity

logger = logging.getLogger(__name__)


class RewardFidelityLevel(str, Enum):
    """Enumeration of reward fidelity levels for coarsening."""
    DENSE = "dense"
    BINARY = "binary"
    THREE_BIN = "3-bin"
    QUATERNARY = "quaternary"  # Included for completeness, though validation may reject in tests if not fully implemented


def coarsen_rewards(
    trajectory: List[Dict[str, Any]],
    fidelity_level: RewardFidelityLevel
) -> List[Dict[str, Any]]:
    """
    Coarsen the reward signals in a trajectory to the specified fidelity level.

    Args:
        trajectory: List of steps, each containing a 'reward' key (float).
        fidelity_level: Target fidelity level (DENSE, BINARY, THREE_BIN).

    Returns:
        A new trajectory list with modified 'reward' values.

    Raises:
        ValueError: If fidelity_level is invalid or not implemented.
    """
    if not isinstance(fidelity_level, RewardFidelityLevel):
        try:
            fidelity_level = RewardFidelityLevel(fidelity_level)
        except ValueError:
            raise ValueError(f"Invalid fidelity_level: {fidelity_level}. "
                             f"Must be one of {[e.value for e in RewardFidelityLevel]}")

    # If dense, return a copy (no change)
    if fidelity_level == RewardFidelityLevel.DENSE:
        return [step.copy() for step in trajectory]

    # Extract original rewards
    rewards = [step.get("reward", 0.0) for step in trajectory]
    if not rewards:
        logger.warning("Empty trajectory or no rewards found.")
        return trajectory

    rewards_np = np.array(rewards)
    min_r, max_r = rewards_np.min(), rewards_np.max()
    range_r = max_r - min_r if max_r > min_r else 1.0

    new_trajectory = []

    for i, step in enumerate(trajectory):
        new_step = step.copy()
        original_reward = rewards_np[i]

        if fidelity_level == RewardFidelityLevel.BINARY:
            # Binary: 0.0 if reward <= 0, 1.0 if reward > 0 (assuming standard 0/1 reward)
            # Or based on median if distribution is unknown? Spec implies standard binary.
            # Let's assume standard: success=1, fail=0 or similar.
            # If continuous, we can threshold at 0 or median.
            # Standard AgentBench often uses 0/1. Let's do > 0.
            new_reward = 1.0 if original_reward > 0.0 else 0.0

        elif fidelity_level == RewardFidelityLevel.THREE_BIN:
            # 3-bin: Low (0-33%), Mid (33-66%), High (66-100%)
            # Normalize to [0, 1]
            normalized = (original_reward - min_r) / range_r
            if normalized < 0.33:
                new_reward = 0.0
            elif normalized < 0.66:
                new_reward = 0.5
            else:
                new_reward = 1.0

        else:
            # Fallback for unimplemented levels (e.g., QUATERNARY)
            raise ValueError(f"Coarsening to {fidelity_level.value} is not yet implemented.")

        new_step["reward"] = new_reward
        new_trajectory.append(new_step)

    return new_trajectory


def identify_pruning_candidates(
    trajectory: List[Dict[str, Any]],
    fidelity_level: RewardFidelityLevel,
    threshold: float = 0.5
) -> List[int]:
    """
    Identify indices in the trajectory that are candidates for pruning
    based on the coarsened reward signal.

    Logic:
    - If BINARY: Prune steps where reward is 0 (failure/low signal).
    - If THREE_BIN: Prune steps where reward is 0.0 (low bin).
    - If DENSE: No pruning candidates (or based on a value threshold).

    Args:
        trajectory: List of steps.
        fidelity_level: The fidelity level used to generate rewards (or to interpret them).
        threshold: Threshold for dense rewards if applicable.

    Returns:
        List of indices to prune.
    """
    candidates = []

    if fidelity_level == RewardFidelityLevel.BINARY:
        for i, step in enumerate(trajectory):
            if step.get("reward", 0.0) == 0.0:
                candidates.append(i)

    elif fidelity_level == RewardFidelityLevel.THREE_BIN:
        for i, step in enumerate(trajectory):
            if step.get("reward", 0.0) == 0.0:
                candidates.append(i)

    elif fidelity_level == RewardFidelityLevel.DENSE:
        for i, step in enumerate(trajectory):
            if step.get("reward", 0.0) < threshold:
                candidates.append(i)

    else:
        raise ValueError(f"Unknown fidelity level: {fidelity_level}")

    return candidates


def prune_trajectory(
    trajectory: List[Dict[str, Any]],
    indices_to_remove: List[int]
) -> List[Dict[str, Any]]:
    """
    Remove specific indices from the trajectory.

    Args:
        trajectory: Original trajectory.
        indices_to_remove: List of indices to remove.

    Returns:
        Pruned trajectory.
    """
    if not indices_to_remove:
        return trajectory.copy()

    remove_set = set(indices_to_remove)
    pruned = [step.copy() for i, step in enumerate(trajectory) if i not in remove_set]
    logger.info(f"Pruned {len(indices_to_remove)} steps. Original: {len(trajectory)}, New: {len(pruned)}")
    return pruned


@contextmanager
def fidelity_context(
    trajectory: List[Dict[str, Any]],
    fidelity_level: RewardFidelityLevel,
    prune: bool = True,
    threshold: float = 0.5
) -> Iterator[Tuple[List[Dict[str, Any]], List[int]]]:
    """
    Context manager to apply reward coarsening and optional pruning to a trajectory.

    This implements the "Dynamic Pruning" logic where the agent's context is modified
    based on the manipulated reward signals.

    Args:
        trajectory: The original trajectory data.
        fidelity_level: The target reward fidelity.
        prune: Whether to actually remove the identified steps.
        threshold: Threshold for dense reward pruning.

    Yields:
        Tuple of (modified_trajectory, removed_indices)
    """
    logger.info(f"Applying fidelity context: {fidelity_level.value}, prune={prune}")

    # 1. Coarsen rewards
    coarsened_trajectory = coarsen_rewards(trajectory, fidelity_level)

    # 2. Identify candidates
    candidates = identify_pruning_candidates(coarsened_trajectory, fidelity_level, threshold)

    if prune:
        # 3. Execute pruning
        final_trajectory = prune_trajectory(coarsened_trajectory, candidates)
    else:
        final_trajectory = coarsened_trajectory

    try:
        yield final_trajectory, candidates
    finally:
        pass  # No cleanup needed for in-memory lists