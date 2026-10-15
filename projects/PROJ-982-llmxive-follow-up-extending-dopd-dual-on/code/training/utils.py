"""
Utility functions for the training regimes.

This module provides the core calculations required by the DOPD training
regime as separate, test‑able functions.  The functions are deliberately
lightweight and have no side‑effects apart from returning a float, making
them easy to import in the unit tests that exercise T022 and T023.
"""

from __future__ import annotations

from typing import List

import numpy as np


def calculate_advantage_gap(
    teacher,
    baseline,
    state: tuple[int, int, int],
    action: int,
) -> float:
    """
    Compute the advantage gap for a given (state, action) pair.

    The advantage gap is defined as::

        Q_teacher(s, a) - V_baseline(s)

    where ``Q_teacher`` comes from the cached optimal Q‑table of the
    ``TeacherOracle`` and ``V_baseline`` is the Monte‑Carlo estimate from
    ``BaselineEstimator``.

    Parameters
    ----------
    teacher
        Instance of :class:`agents.teacher.TeacherOracle`.
    baseline
        Instance of :class:`agents.baseline_estimator.BaselineEstimator`.
    state
        Full state tuple ``(x, y, h)`` as used by the teacher.
    action
        Integer action index.

    Returns
    -------
    float
        The advantage gap.  If for any reason the teacher or baseline does
        not provide a value, the function returns ``0.0`` (a safe default
        that does not break training).
    """
    try:
        q_val = teacher.get_q_value(state, action)
    except Exception:
        q_val = 0.0

    try:
        v_val = baseline.get_v_baseline(state)
    except Exception:
        v_val = 0.0

    return float(q_val - v_val)


def calculate_dynamic_lambda(gap_batch: List[float]) -> float:
    """
    Compute a dynamic λ weighting based on a rolling batch of advantage gaps.

    The behaviour follows the specification in the plan:

    * If the dynamic range ``max(gap) - min(gap)`` is **< 0.1**, perform
      min‑max normalisation of the *most recent* gap.
    * Otherwise, apply a sigmoid scaling to the most recent gap.
    * In the degenerate case where the range is zero (all gaps identical),
      fall back to ``λ = 1.0`` and the caller may log a ``lambda_switch``
      event.

    The function returns a λ value clamped to the interval ``[0.1, 1.0]``,
    matching the limits used elsewhere in the training code.

    Parameters
    ----------
    gap_batch
        List of recent advantage‑gap values (ordered chronologically).

    Returns
    -------
    float
        The dynamically computed λ.
    """
    if len(gap_batch) < 2:
        # Not enough information – default to uniform weighting.
        return 1.0

    min_gap = min(gap_batch)
    max_gap = max(gap_batch)
    dynamic_range = max_gap - min_gap
    adaptive_threshold = 0.1

    # Use the most recent gap as the signal.
    recent_gap = gap_batch[-1]

    if dynamic_range < adaptive_threshold:
        # Min‑max normalisation path.
        if dynamic_range == 0:
            # All gaps identical – cannot normalise.
            lambda_val = 1.0
        else:
            lambda_val = (recent_gap - min_gap) / (dynamic_range + 1e-8)
    else:
        # Sigmoid scaling path.
        lambda_val = 1.0 / (1.0 + np.exp(-recent_gap))

    # Clamp to the allowed interval.
    lambda_val = max(0.1, min(1.0, lambda_val))
    return float(lambda_val)