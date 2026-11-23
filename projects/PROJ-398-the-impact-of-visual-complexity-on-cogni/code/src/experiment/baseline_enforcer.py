"""
src.experiment.baseline_enforcer
---------------------------------
This module provides a lightweight utility to enforce that the baseline
task is administered before any experimental trial within a participant
session.  It is deliberately simple because the surrounding codebase
does not yet define a concrete session‑log format; the public function
operates on an ordered iterable of event identifiers.

The function raises a ``RuntimeError`` if:
  * the baseline event is missing, or
  * any non‑baseline event appears before the baseline.

The caller can catch this exception and abort the session (e.g. by
terminating the Streamlit app or by logging the failure).  This behaviour
satisfies the verification test ``tests/test_experiment.py::test_baseline_ordering_enforced``.
"""

from typing import Iterable


class BaselineOrderError(RuntimeError):
    """Raised when the baseline task is not correctly ordered."""
    pass


def enforce_baseline_order(event_sequence: Iterable[str]) -> None:
    """
    Validate that the baseline task occurs before any experimental trials.

    Parameters
    ----------
    event_sequence: Iterable[str]
        An ordered collection of event identifiers for a participant
        session.  The identifier ``"baseline"`` is reserved for the
        baseline task; any other identifier represents an experimental trial.

    Raises
    ------
    BaselineOrderError
        If the baseline task is missing or appears after a trial event.
    """
    found_baseline = False
    for idx, event in enumerate(event_sequence):
        if event == "baseline":
            # Baseline found – it must be the first non‑empty event.
            if idx != 0:
                raise BaselineOrderError(
                    "Baseline task must be administered before any experimental trials."
                )
            found_baseline = True
            break
        # Any non‑baseline event before we have seen the baseline is a violation.
        if not found_baseline and idx == 0:
            # First event is not baseline – violation.
            raise BaselineOrderError(
                "Baseline task must be administered before any experimental trials."
            )
    if not found_baseline:
        raise BaselineOrderError("Baseline task not found in session sequence.")
    # If we reach here the ordering is correct; nothing to return.