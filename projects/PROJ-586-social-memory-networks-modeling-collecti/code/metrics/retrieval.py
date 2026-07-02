"""
Retrieval metric utilities for the Social Memory Networks project.

This module defines:
  - ``RetrievalMetrics``: a dataclass container for the raw counts and derived
    rates.
  - ``compute_retrieval_rate``: simple proportion of successful retrievals.
  - ``compute_retrieval_efficiency``: proportion of the observed retrieval rate
    relative to the naïve baseline (1 / N_agents).  The function is defensive:
    it validates inputs, raises informative ``ValueError`` on nonsensical
    arguments, and never returns ``nan`` or ``inf``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

__all__ = [
    "RetrievalMetrics",
    "compute_retrieval_rate",
    "compute_retrieval_efficiency",
]


@dataclass(frozen=True)
class RetrievalMetrics:
    """
    Container for the raw counts and derived statistics of a single game's
    retrieval performance.

    Attributes
    ----------
    correct : int
        Number of successful cue‑retrieval events.
    total : int
        Total number of retrieval attempts made.
    num_agents : int
        Number of agents that participated in the game.
    rate : float
        ``correct / total`` (0.0 if ``total`` is 0).
    baseline : float
        The naïve baseline success probability, defined as ``1 / num_agents``
        (0.0 if ``num_agents`` is 0).
    """
    correct: int
    total: int
    num_agents: int
    rate: float
    baseline: float


def _validate_inputs(correct: int, total: int, num_agents: int) -> None:
    """
    Validate the three integer inputs used by the retrieval functions.

    The contract required by the test‑suite is:
      * ``correct``, ``total`` and ``num_agents`` must be non‑negative integers.
      * ``correct`` cannot exceed ``total``.
      * ``total`` must be positive when ``correct`` > 0 (otherwise the rate is
        defined as 0.0).
      * ``num_agents`` must be positive for a meaningful baseline; a value of
        0 results in a baseline of 0.0 and an efficiency of 0.0.

    Any violation raises ``ValueError`` with a clear message.
    """
    if not isinstance(correct, int):
        raise ValueError(f"`correct` must be int, got {type(correct)}")
    if not isinstance(total, int):
        raise ValueError(f"`total` must be int, got {type(total)}")
    if not isinstance(num_agents, int):
        raise ValueError(f"`num_agents` must be int, got {type(num_agents)}")

    if correct < 0:
        raise ValueError("`correct` cannot be negative")
    if total < 0:
        raise ValueError("`total` cannot be negative")
    if num_agents < 0:
        raise ValueError("`num_agents` cannot be negative")
    if correct > total:
        raise ValueError("`correct` cannot be greater than `total`")
    # ``total`` may be zero (e.g., no retrieval attempts).  In that case
    # ``correct`` must also be zero – the check above already guarantees that.
    # ``num_agents`` may be zero; the baseline will be defined as 0.0, which
    # downstream code treats as “no baseline possible”.



def compute_retrieval_rate(correct: int, total: int) -> float:
    """
    Compute the raw retrieval rate for a single game.

    Parameters
    ----------
    correct : int
        Number of successful retrievals.
    total : int
        Number of retrieval attempts.

    Returns
    -------
    float
        ``correct / total`` if ``total`` > 0, otherwise ``0.0``.
    """
    _validate_inputs(correct, total, num_agents=1)  # ``num_agents`` dummy for validation
    if total == 0:
        return 0.0
    return correct / total


def compute_retrieval_efficiency(
    correct: int,
    total: int,
    num_agents: int,
) -> Tuple[RetrievalMetrics, float]:
    """
    Compute the cue‑retrieval efficiency metric.

    The efficiency is defined as the ratio between the observed retrieval rate
    and the naïve baseline ``1 / num_agents``:

        efficiency = (correct / total) / (1 / num_agents)

    If ``total`` or ``num_agents`` are zero, the efficiency is defined as ``0.0``.

    Parameters
    ----------
    correct : int
        Number of successful retrievals.
    total : int
        Total number of retrieval attempts.
    num_agents : int
        Number of agents participating in the experiment.

    Returns
    -------
    Tuple[RetrievalMetrics, float]
        ``RetrievalMetrics`` instance containing the raw counts and derived
        rates, and the efficiency value.

    Raises
    ------
    ValueError
        If any of the inputs are negative, non‑integer, or if ``correct`` >
        ``total``.
    """
    # Validate inputs first – this also guarantees ``correct`` ≤ ``total``.
    _validate_inputs(correct, total, num_agents)

    # Compute the observed retrieval rate.
    rate = correct / total if total > 0 else 0.0

    # Compute the baseline (naïve chance of guessing the correct cue).
    baseline = 1.0 / num_agents if num_agents > 0 else 0.0

    # Efficiency is the ratio of observed rate to baseline.
    efficiency = (rate / baseline) if baseline > 0 else 0.0

    metrics = RetrievalMetrics(
        correct=correct,
        total=total,
        num_agents=num_agents,
        rate=rate,
        baseline=baseline,
    )
    return metrics, efficiency
