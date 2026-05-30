"""T017 — Safe computational evaluator (spec 018, FR-014/015).

Placeholder module so the verify package imports cleanly.
Full implementation is in Phase 5 (T016/T017).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from llmxive.claims.models import Claim


class ComputeStatus(str, Enum):
    VERIFIED = "verified"
    REFUTED = "refuted"
    NOT_EVALUABLE = "not_evaluable"


@dataclass(frozen=True)
class ComputeVerdict:
    evaluable: bool
    status: ComputeStatus
    asserted: str
    computed: str
    expression: str


def evaluate(expression: str) -> Optional[str]:
    """Evaluate *expression* safely using sympy. Returns None if not parseable.

    Uses sympy (NOT eval/exec). Full implementation: Phase 5 T017.
    """
    try:
        import sympy
        result = sympy.sympify(expression)
        return str(result)
    except Exception:
        return None


def extract_expression(
    claim: "Claim",
    *,
    backend,
    model: Optional[str],
    repo_root: Optional[str],
) -> Optional[tuple[str, str]]:
    """Use the LLM backend to locate the expression and asserted result in *claim*.

    Returns (expression, asserted_result) or None if not locatable.
    Full implementation: Phase 5 T017.
    """
    raise NotImplementedError("extract_expression requires Phase 5 T017 implementation")


def verify_computational(
    claim: "Claim",
    *,
    backend,
    model: Optional[str] = None,
    repo_root: Optional[str] = None,
) -> ComputeVerdict:
    """Verify a self-contained claim by sympy evaluation.

    Full implementation: Phase 5 T017.
    """
    raise NotImplementedError("verify_computational requires Phase 5 T017 implementation")


__all__ = [
    "ComputeStatus",
    "ComputeVerdict",
    "evaluate",
    "extract_expression",
    "verify_computational",
]
