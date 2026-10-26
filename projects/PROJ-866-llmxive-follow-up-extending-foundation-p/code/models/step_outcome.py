"""
code.models.step_outcome
------------------------

Definition of the ``StepOutcome`` data model used to represent a single
step‑level outcome derived from an execution log.  The model is a plain
Python ``dataclass`` that mirrors the fields required by the
``step_expander`` utility and the downstream GEE regression analysis.

Fields
------
workflow_id: str
    Identifier of the workflow to which the step belongs.
step_index: int
    Index of the step within the workflow (0‑based).  The current
    implementation treats each execution log as a single step, so this
    is always ``0``.
outcome: int
    Binary outcome – ``0`` if the workflow had no policy violations,
    ``1`` otherwise.
context_reduction_pct: int | float | str
    The context reduction percentage for the step.  Numeric values are
    ``0``‑``100``; the sentinel string ``"[deferred]"`` is used for edge
    cases where a reduction cannot be computed.
policy_complexity: int | float
    The ``complexity`` field from the original execution log.
delegation_depth: int | float
    The ``depth`` field from the original execution log.
exclude_from_regression: bool
    ``True`` when ``context_reduction_pct`` is ``"[deferred]"`` – such rows
    must be omitted from the GEE regression.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Union

@dataclass
class StepOutcome:
    """Dataclass representing a single step‑level outcome."""

    workflow_id: str
    step_index: int
    outcome: int
    context_reduction_pct: Union[int, float, str]
    policy_complexity: Union[int, float]
    delegation_depth: Union[int, float]
    exclude_from_regression: bool

    def to_dict(self) -> dict:
        """Return a plain ``dict`` representation suitable for JSON serialisation."""
        return asdict(self)

__all__ = ["StepOutcome"]