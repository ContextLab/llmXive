"""Shared auditor scaffold for spec 009.

Single source of truth (Constitution Principle I) for the four auditors:
  - personality_rubric : FR-004, FR-005
  - template_vs_real   : FR-006, FR-007
  - pdf                : FR-012, FR-013
  - feedback_loop      : FR-034

Each auditor is a sibling module; `run_audit(name, ...)` dispatches to the
right one. Output manifests are written via `manifest.write_manifest(...)`.
"""

from __future__ import annotations

from typing import Any

__version__ = "0.1.0"

_REGISTRY: dict[str, Any] = {}  # auditor-name -> callable(**kwargs) -> dict[str, Any]


def register(name: str, fn: Any) -> None:
    """Register an auditor entry point. Called by each auditor module on import."""
    _REGISTRY[name] = fn


def run_audit(name: str, **kwargs: Any) -> dict[str, Any]:
    """Dispatch to the named auditor and return its manifest dict."""
    if name not in _REGISTRY:
        raise KeyError(
            f"Unknown auditor: {name!r}. Registered: {sorted(_REGISTRY)}. "
            f"Did you forget to import the auditor module?"
        )
    result: dict[str, Any] = _REGISTRY[name](**kwargs)
    return result


# Import sub-modules so they self-register. Done at end to avoid circular imports.
from . import (  # noqa: E402  (deferred to break the auditor<->package cycle)
    feedback_loop,  # noqa: F401
    manifest,  # noqa: F401
    pdf_auditor,  # noqa: F401
    personality_rubric,  # noqa: F401
    template_vs_real,  # noqa: F401
)

# Spec 010 re-exports (single-source-of-truth shortcuts for callers).
from .liveness import check_pointer  # noqa: E402,F401
from .speckit_prune import audit_artifacts, prune_templates  # noqa: E402,F401
