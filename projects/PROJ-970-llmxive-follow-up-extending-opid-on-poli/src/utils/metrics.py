"""
Utility metrics module for OPID routing complexity analysis.

Provides pure‑CPU functions for:
- Shannon entropy calculations
- Log‑probability shift computation
- Success‑rate determination for a trajectory vs. ground‑truth path
- Miscellaneous statistical helpers used throughout the code base and tests
"""

from __future__ import annotations

import hashlib
from collections import Counter, namedtuple
from typing import Iterable, List, Sequence, Tuple

import numpy as np

# ----------------------------------------------------------------------
# Named result types
# ----------------------------------------------------------------------
SuccessRateResult = namedtuple("SuccessRateResult", ["success_count", "rate"])


# ----------------------------------------------------------------------
# Entropy utilities
# ----------------------------------------------------------------------
def entropy(probs: Sequence[float]) -> float:
    """
    Compute the Shannon entropy (in bits) of a probability distribution.

    Parameters
    ----------
    probs : Sequence[float]
        Probabilities that should sum to 1. Zero probabilities are ignored.

    Returns
    -------
    float
        Entropy in bits. Returns 0.0 for an empty or all‑zero input.
    """
    # Convert to numpy array for vectorised operations
    probs_arr = np.asarray(probs, dtype=float)

    # Guard against empty input
    if probs_arr.size == 0:
        return 0.0

    # Filter out non‑positive entries to avoid log(0)
    positive = probs_arr[probs_arr > 0]

    if positive.size == 0:
        return 0.0

    # Shannon entropy (bits)
    return float(-np.sum(positive * np.log2(positive)))


def calculate_raw_entropy(values: Sequence[float]) -> float:
    """
    Alias for :func:`entropy` that works directly on a list of probabilities.
    Kept for compatibility with existing test suite.
    """
    return entropy(values)


# ----------------------------------------------------------------------
# Action‑entropy helpers (used by policy tests)
# ----------------------------------------------------------------------
def calculate_action_entropy(actions: Sequence[int]) -> float:
    """
    Compute the entropy of a sequence of discrete actions.

    The function treats the input as a categorical distribution over the
    observed actions and returns the Shannon entropy in bits.

    Parameters
    ----------
    actions : Sequence[int]
        List of action identifiers (e.g., integers).

    Returns
    -------
    float
        Entropy in bits; 0.0 when the list is empty or all actions are identical.
    """
    if not actions:
        return 0.0

    counts = Counter(actions)
    total = sum(counts.values())
    probs = [cnt / total for cnt in counts.values()]
    return entropy(probs)


# ----------------------------------------------------------------------
# Log‑probability shift utilities
# ----------------------------------------------------------------------
def log_prob_shift(original: float, injected: float) -> float:
    """
    Compute the additive log‑probability shift introduced by an injection.

    The shift is defined as ``log(injected) - log(original)``.
    If either argument is non‑positive, the function returns 0.0 because
    a log‑probability is undefined for those values.

    Parameters
    ----------
    original : float
        Original probability (must be > 0).
    injected : float
        Injected probability (must be > 0).

    Returns
    -------
    float
        The log‑probability shift; 0.0 when inputs are invalid.
    """
    if original <= 0 or injected <= 0:
        return 0.0
    return float(np.log(injected) - np.log(original))


def calculate_mean_log_prob_shift(shifts: Sequence[float]) -> float:
    """
    Compute the arithmetic mean of a collection of log‑probability shifts.

    Returns 0.0 for an empty input sequence.
    """
    if not shifts:
        return 0.0
    return float(np.mean(shifts))


# ----------------------------------------------------------------------
# Success‑rate utilities
# ----------------------------------------------------------------------
def _is_subsequence(sub: Sequence[int], seq: Sequence[int]) -> bool:
    """
    Helper that checks whether ``sub`` appears as a subsequence of ``seq``
    preserving order but not necessarily contiguity.
    """
    it = iter(seq)
    return all(item in it for item in sub)


def calculate_success_rate(
    trajectory: Sequence[int],
    ground_truth: Sequence[int],
) -> SuccessRateResult:
    """
    Determine whether a trajectory successfully reproduces the ground‑truth
    path and return a ``SuccessRateResult``.

    The success definition follows the unit‑test expectations:
    - If ``ground_truth`` is empty, success is ``False`` (rate 0.0).
    - Success is ``True`` when ``ground_truth`` appears as an ordered
      subsequence of ``trajectory``.
    - Otherwise success is ``False``.

    Parameters
    ----------
    trajectory : Sequence[int]
        The sequence of visited node identifiers produced by the agent.
    ground_truth : Sequence[int]
        The reference path that defines a successful episode.

    Returns
    -------
    SuccessRateResult
        ``success_count`` is ``1`` for success, ``0`` otherwise.
        ``rate`` is ``1.0`` for success, ``0.0`` otherwise.
    """
    if not ground_truth:
        return SuccessRateResult(success_count=0, rate=0.0)

    success = _is_subsequence(ground_truth, trajectory)
    return SuccessRateResult(success_count=int(success), rate=1.0 if success else 0.0)


# ----------------------------------------------------------------------
# Statistical helpers
# ----------------------------------------------------------------------
def calculate_mean_entropy(entropy_values: Sequence[float]) -> float:
    """
    Compute the arithmetic mean of a collection of entropy values.
    Returns 0.0 for an empty collection.
    """
    if not entropy_values:
        return 0.0
    return float(np.mean(entropy_values))


def calculate_variance(values: Sequence[float]) -> float:
    """
    Compute the population variance of a list of numbers.
    Returns 0.0 for empty or single‑element inputs.
    """
    if not values:
        return 0.0
    arr = np.asarray(values, dtype=float)
    if arr.size == 1:
        return 0.0
    mean = np.mean(arr)
    return float(np.mean((arr - mean) ** 2))


# ----------------------------------------------------------------------
# File checksum utility
# ----------------------------------------------------------------------
def calculate_checksum(file_path: str) -> str:
    """
    Compute a SHA‑256 checksum of the file at ``file_path``.

    Parameters
    ----------
    file_path : str
        Path to the file whose checksum should be computed.

    Returns
    -------
    str
        Hex‑encoded SHA‑256 digest (64 characters).

    Raises
    ------
    FileNotFoundError
        If ``file_path`` does not point to an existing file.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


# ----------------------------------------------------------------------
# Cost‑benefit ratio helper
# ----------------------------------------------------------------------
def calculate_distillation_cost_benefit_ratio(
    mean_log_prob_shift: float,
    success_rate_held_out: float,
    baseline_success_rate: float,
) -> float:
    """
    Compute the ratio of average log‑probability shift to the improvement
    in success rate over a baseline.

    The denominator is ``success_rate_held_out - baseline_success_rate``.
    If this improvement is zero or negative, the function returns
    ``float('inf')`` to indicate an undefined or infinitely large ratio,
    matching the expectations of the test suite.

    Parameters
    ----------
    mean_log_prob_shift : float
        Mean log‑probability shift observed on the held‑out set.
    success_rate_held_out : float
        Success rate measured on the held‑out validation data.
    baseline_success_rate : float
        Success rate for the baseline (threshold = 1.0).

    Returns
    -------
    float
        The cost‑benefit ratio, or ``inf`` when the denominator ≤ 0.
    """
    improvement = success_rate_held_out - baseline_success_rate
    if improvement <= 0:
        return float("inf")
    return mean_log_prob_shift / improvement


# ----------------------------------------------------------------------
# Export list for ``__all__`` (helps static analysis)
# ----------------------------------------------------------------------
__all__ = [
    "SuccessRateResult",
    "entropy",
    "calculate_raw_entropy",
    "calculate_action_entropy",
    "log_prob_shift",
    "calculate_mean_log_prob_shift",
    "calculate_success_rate",
    "calculate_mean_entropy",
    "calculate_variance",
    "calculate_checksum",
    "calculate_distillation_cost_benefit_ratio",
]