"""
Unit test for the StepOutcome data model required by FR‑005.
The model is defined as a simple dataclass with type‑annotated fields.
"""

from dataclasses import dataclass
from typing import Literal, Union

@dataclass
class StepOutcome:
    """
    Represents a single step outcome in the expanded step‑level dataset.

    Attributes
    ----------
    workflow_id: str
        Identifier of the workflow this step belongs to.
    step_index: int
        Zero‑based index of the step within the workflow.
    outcome: Literal[0, 1]
        Binary outcome where 1 indicates a policy‑violation error,
        0 indicates correct execution.
    context_reduction_pct: Union[float, Literal["[deferred]"]]
        Percentage reduction of context compared to the full‑context baseline.
    policy_complexity: int
        Complexity metric of the policy graph for this step.
    delegation_depth: int
        Depth of delegation chain for this step.
    exclude_from_regression: bool
        Flag indicating whether this row should be excluded from the
        regression dataset (e.g., when ``context_reduction_pct`` is
        ``"[deferred]"``).
    """
    workflow_id: str
    step_index: int
    outcome: Literal[0, 1]
    context_reduction_pct: Union[float, Literal["[deferred]"]]
    policy_complexity: int
    delegation_depth: int
    exclude_from_regression: bool