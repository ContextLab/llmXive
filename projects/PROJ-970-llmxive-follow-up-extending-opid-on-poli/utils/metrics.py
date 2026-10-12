"""
Utility functions for metric calculations used throughout the OPID routing
complexity analysis project.

This module re‑exports all symbols from the original implementation located in
``code.utils.metrics`` (the canonical source of metric helpers) and adds a
small convenience wrapper for per‑episode statistics that matches the
``episode_result.schema.yaml`` contract.

The public API includes:
  - ``entropy(probs)`` – Shannon entropy (natural log) of a probability vector.
  - ``log_prob_shift(original, injected)`` – sum of log‑probability differences.
  - ``compute_episode_statistics(action_prob_steps, injected_prob_steps=None)`` –
    aggregates per‑step metrics into episode‑level totals.
  - All other helpers originally defined in ``code.utils.metrics`` (e.g.
    ``calculate_success_rate``, ``calculate_raw_entropy``, etc.) are re‑exported
    unchanged.
"""

from __future__ import annotations

import importlib
from typing import List, Sequence

import numpy as np

# ----------------------------------------------------------------------
# Re‑export everything from the original implementation in ``code.utils.metrics``.
# ----------------------------------------------------------------------
_code_metrics = importlib.import_module("code.utils.metrics")
# Export all public attributes (those that do not start with an underscore).
for _name in dir(_code_metrics):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_code_metrics, _name)

# ----------------------------------------------------------------------
# Metric helpers required by the task specification.
# ----------------------------------------------------------------------
def entropy(probs: Sequence[float] | np.ndarray) -> float:
    """
    Compute the Shannon entropy of a probability distribution.

    Parameters
    ----------
    probs : sequence or np.ndarray
        Probabilities that sum to 1. Zero entries are ignored in the
        ``p * log(p)`` term to avoid ``log(0)``.

    Returns
    -------
    float
        Entropy in nats (natural logarithm). Returns ``0.0`` for an empty
        or degenerate distribution.
    """
    probs_arr = np.asarray(probs, dtype=float)
    # Guard against empty input
    if probs_arr.size == 0:
        return 0.0
    # Normalise just in case (does not affect zero entries)
    total = probs_arr.sum()
    if total == 0:
        return 0.0
    probs_arr = probs_arr / total
    # Use mask to avoid log(0)
    mask = probs_arr > 0
    return -float(np.sum(probs_arr[mask] * np.log(probs_arr[mask])))

def log_prob_shift(original: Sequence[float] | np.ndarray,
                   injected: Sequence[float] | np.ndarray) -> float:
    """
    Compute the total shift in log‑probability between two probability vectors.

    The shift is defined as ``sum(log(injected_i) - log(original_i))``.
    Zero probabilities are ignored (they contribute ``0`` to the sum).

    Parameters
    ----------
    original : sequence or np.ndarray
        Original probability distribution.
    injected : sequence or np.ndarray
        Probability distribution after skill‑signal injection.

    Returns
    -------
    float
        Sum of per‑action log‑probability differences. Returns ``0.0`` if
        both inputs are empty or contain only zeros.
    """
    orig_arr = np.asarray(original, dtype=float)
    inj_arr = np.asarray(injected, dtype=float)

    # Normalise to protect against malformed input
    if orig_arr.size == 0 or inj_arr.size == 0:
        return 0.0

    # Avoid division by zero / log(0) by masking positive entries
    mask = (orig_arr > 0) & (inj_arr > 0)
    if not np.any(mask):
        return 0.0

    log_orig = np.log(orig_arr[mask])
    log_inj = np.log(inj_arr[mask])
    return float(np.sum(log_inj - log_orig))

def compute_episode_statistics(
    action_prob_steps: List[Sequence[float] | np.ndarray],
    injected_prob_steps: List[Sequence[float] | np.ndarray] | None = None,
) -> dict:
    """
    Aggregate per‑step action probabilities into episode‑level statistics.

    The returned dictionary contains the fields required by
    ``episode_result.schema.yaml`` (as used by the runner implementation):
      - ``action_entropy_sum`` : total entropy accumulated over the episode.
      - ``log_prob_shift_sum`` : total log‑probability shift over the episode.
      - ``injection_count``   : number of steps where an injection occurred
                                (i.e., where ``injected_prob_steps`` is provided).

    Parameters
    ----------
    action_prob_steps : list
        Sequence of probability vectors (one per step) produced by the policy.
    injected_prob_steps : list or None
        Optional sequence of probability vectors after injection. If omitted,
        the log‑probability shift is assumed to be ``0`` for all steps.

    Returns
    -------
    dict
        Mapping with the three aggregated metrics.
    """
    if not action_prob_steps:
        # No steps – return zeros to keep downstream code happy.
        return {
            "action_entropy_sum": 0.0,
            "log_prob_shift_sum": 0.0,
            "injection_count": 0,
        }

    # Compute entropy for each step and sum.
    entropy_sum = 0.0
    for probs in action_prob_steps:
        entropy_sum += entropy(probs)

    # Compute log‑probability shift if injected distributions are supplied.
    if injected_prob_steps is None:
        log_shift_sum = 0.0
        injection_cnt = 0
    else:
        if len(injected_prob_steps) != len(action_prob_steps):
            raise ValueError(
                "Length of injected_prob_steps must match action_prob_steps"
            )
        log_shift_sum = 0.0
        injection_cnt = 0
        for orig, inj in zip(action_prob_steps, injected_prob_steps):
            # Only count a shift when the injected distribution differs.
            if not np.allclose(orig, inj):
                injection_cnt += 1
                log_shift_sum += log_prob_shift(orig, inj)

    return {
        "action_entropy_sum": float(entropy_sum),
        "log_prob_shift_sum": float(log_shift_sum),
        "injection_count": int(injection_cnt),
    }