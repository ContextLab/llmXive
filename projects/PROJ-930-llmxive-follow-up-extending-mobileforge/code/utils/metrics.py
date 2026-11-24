"""
utils/metrics.py

Lightweight metric calculation utilities required for the MobileForge
logic distillation evaluation pipeline.

This module defines two simple metric classes:
  * ``SuccessRate`` – computes the proportion of successful tasks.
  * ``StepEfficiency`` – computes the ratio of average steps taken to
    average optimal steps (a non‑negative value).

The implementation follows the exact public interface required by the
unit tests (see ``code/tests/unit/test_metrics.py``) and the task
description in ``tasks.md``.
"""

from typing import List


class SuccessRate:
    """
    Compute the success rate for a list of boolean success flags.

    The success rate is defined as the number of ``True`` entries divided
    by the total number of entries.  An empty input list yields ``0.0``.
    """

    def compute(self, success_flags: List[bool]) -> float:
        """
        Parameters
        ----------
        success_flags: List[bool]
            List where each element indicates whether a task succeeded.

        Returns
        -------
        float
            Success rate in the range ``[0.0, 1.0]``.  Returns ``0.0`` for
            an empty list.
        """
        if not success_flags:
            return 0.0
        successful = sum(1 for flag in success_flags if flag)
        total = len(success_flags)
        return successful / total


class StepEfficiency:
    """
    Compute step efficiency as the ratio of average steps taken to average
    optimal steps.

    The metric is defined only for matching ``steps_taken`` and
    ``optimal_steps`` sequences.  If either list is empty, or the average
    optimal step count is zero, the method returns ``0.0`` to avoid a
    division‑by‑zero error.  A ``ValueError`` is raised when the input
    sequences have different lengths.
    """

    def compute(self, steps_taken: List[int], optimal_steps: List[int]) -> float:
        """
        Parameters
        ----------
        steps_taken: List[int]
            Actual number of steps taken by the model for each task.
        optimal_steps: List[int]
            Optimal (minimal) number of steps for the same tasks.

        Returns
        -------
        float
            Non‑negative step‑efficiency value.  ``0.0`` is returned when
            the metric cannot be computed (empty inputs or zero average
            optimal steps).

        Raises
        ------
        ValueError
            If ``steps_taken`` and ``optimal_steps`` are of different
            lengths.
        """
        if not steps_taken or not optimal_steps:
            return 0.0
        if len(steps_taken) != len(optimal_steps):
            raise ValueError(
                "steps_taken and optimal_steps must have the same length"
            )
        avg_taken = sum(steps_taken) / len(steps_taken)
        avg_optimal = sum(optimal_steps) / len(optimal_steps)
        if avg_optimal == 0:
            return 0.0
        return avg_taken / avg_optimal
