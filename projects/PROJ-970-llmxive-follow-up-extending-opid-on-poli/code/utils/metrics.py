"""
Utility functions for metric calculations used throughout the OPID routing
complexity analysis project.

This module provides pure‑CPU helper functions that operate on probability
vectors produced by policies and on per‑episode result dictionaries.

Functions
---------
- entropy(probs): Compute the Shannon entropy of a probability vector.
- log_prob_shift(original, injected): Compute the average log‑probability
  shift introduced when a skill signal is injected.
- compute_episode_statistics(action_probs, injected_probs, success, steps):
  Aggregate per‑step probabilities into the episode‑level statistics that
  match ``episode_result.schema.yaml``.
- calculate_success_rate(results): Return the fraction of episodes that
  succeeded (i.e. ``result['success'] is True``).
"""

from __future__ import annotations

from typing import List, Sequence, Dict, Any

import numpy as np

__all__ = [
    "entropy",
    "log_prob_shift",
    "compute_episode_statistics",
    "calculate_success_rate",
]


def entropy(probs: Sequence[float] | np.ndarray) -> float:
    """
    Compute the Shannon entropy of a probability distribution.

    Parameters
    ----------
    probs : Sequence[float] | np.ndarray
        A 1‑D array or list of probabilities that sum (approximately) to 1.
        Zero probabilities are allowed and are treated as contributing
        zero to the entropy.

    Returns
    -------
    float
        The entropy in nats (natural logarithm base).

    Notes
    -----
    The implementation guards against ``log(0)`` by using ``np.where``.
    """
    probs_arr = np.asarray(probs, dtype=float)
    if probs_arr.ndim != 1:
        raise ValueError("entropy expects a 1‑D probability vector")
    # Clip tiny negative values that can arise from floating‑point noise
    probs_arr = np.clip(probs_arr, 0.0, 1.0)

    # Avoid log(0) by selecting only positive entries
    positive = probs_arr > 0
    entropy_val = -np.sum(probs_arr[positive] * np.log(probs_arr[positive]))
    return float(entropy_val)


def log_prob_shift(original: Sequence[float] | np.ndarray,
                   injected: Sequence[float] | np.ndarray) -> float:
    """
    Compute the average log‑probability shift introduced by injection.

    For each action the shift is ``log(injected) - log(original)``.
    The function returns the mean shift across all actions.

    Parameters
    ----------
    original : Sequence[float] | np.ndarray
        Original probability distribution before injection.
    injected : Sequence[float] | np.ndarray
        Probability distribution after injection.

    Returns
    -------
    float
        Mean log‑probability shift (in nats). Positive values indicate that
        the injected distribution places higher probability mass on the
        selected actions relative to the original distribution.

    Raises
    ------
    ValueError
        If the two input vectors have different shapes.
    """
    orig_arr = np.asarray(original, dtype=float)
    inj_arr = np.asarray(injected, dtype=float)

    if orig_arr.shape != inj_arr.shape:
        raise ValueError("original and injected must have the same shape")

    # Guard against zeros – replace zero with a very small epsilon to keep log finite
    epsilon = np.finfo(float).eps
    orig_safe = np.where(orig_arr > 0, orig_arr, epsilon)
    inj_safe = np.where(inj_arr > 0, inj_arr, epsilon)

    shift = np.log(inj_safe) - np.log(orig_safe)
    mean_shift = np.mean(shift)
    return float(mean_shift)


def compute_episode_statistics(
    action_probs: List[Sequence[float] | np.ndarray],
    injected_probs: List[Sequence[float] | np.ndarray],
    success: bool,
    steps: int,
) -> Dict[str, Any]:
    """
    Aggregate per‑step probability vectors into episode‑level statistics.

    The returned dictionary conforms to ``episode_result.schema.yaml``.
    Expected keys (as of the current specification) are:

    - ``success`` (bool): Whether the episode reached the goal.
    - ``steps_taken`` (int): Number of steps executed (capped by the
      environment's max‑step limit).
    - ``average_action_entropy`` (float): Mean Shannon entropy of the
      action distributions across all steps.
    - ``average_log_prob_shift`` (float): Mean log‑probability shift across
      all steps (zero if no injection occurred).

    Parameters
    ----------
    action_probs : List[Sequence[float] | np.ndarray]
        List of probability vectors produced by the policy at each step.
    injected_probs : List[Sequence[float] | np.ndarray]
        List of probability vectors after optional OPID injection at each
        step. Must be the same length as ``action_probs``.
    success : bool
        Episode success flag.
    steps : int
        Number of steps taken in the episode.

    Returns
    -------
    dict
        Episode‑level statistics ready for CSV/JSON serialization.
    """
    if len(action_probs) != len(injected_probs):
        raise ValueError(
            "action_probs and injected_probs must have the same length"
        )
    if steps != len(action_probs):
        # ``steps`` may be less than the length if the episode terminated early.
        # In that case we truncate the lists to ``steps``.
        action_probs = action_probs[:steps]
        injected_probs = injected_probs[:steps]

    # Compute per‑step entropies and shifts
    entropies = [entropy(p) for p in action_probs]
    shifts = [
        log_prob_shift(orig, inj) for orig, inj in zip(action_probs, injected_probs)
    ]

    avg_entropy = float(np.mean(entropies)) if entropies else 0.0
    avg_shift = float(np.mean(shifts)) if shifts else 0.0

    return {
        "success": bool(success),
        "steps_taken": int(steps),
        "average_action_entropy": avg_entropy,
        "average_log_prob_shift": avg_shift,
    }


def calculate_success_rate(results: List[Dict[str, Any]]) -> float:
    """
    Compute the success rate for a collection of episode results.

    Parameters
    ----------
    results : List[Dict[str, Any]]
        List of episode result dictionaries (as produced by
        ``compute_episode_statistics`` or loaded from the CSV).

    Returns
    -------
    float
        Fraction of episodes where ``result['success']`` is ``True``.
        Returns ``0.0`` for an empty input list.
    """
    if not results:
        return 0.0
    successes = sum(1 for r in results if r.get("success"))
    return successes / len(results)