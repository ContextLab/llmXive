"""Tests for PaperImplementReviser's missing-tasks.md short-circuit.

Calibration run 26615534442 crashed with:

  PaperImplementReviser: backend did not return parseable JSON:
    notes: No tasks.md provided - cannot execute dispatcher workflow

Root cause: the paper_implementer prompt is a [kind:<value>]
dispatcher that requires tasks.md to route work. The calibration set
supplies paper artifacts only (no tasks.md). The LLM correctly
responded 'No tasks.md provided' as YAML — but the reviser parser
expected JSON, so the response wasn't even parseable as the failure
verdict.

Fix: short-circuit BEFORE the LLM call when no __tasks_md__ is
supplied. Return a structured ConcernResponse per concern with a
clear 'cannot dispatch' note; let the engine decide whether to
kickback based on the panel concerns alone.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.convergence.revisers.paper_implement_reviser import (
    PaperImplementReviser,
)
from llmxive.convergence.types import Concern, Severity


class _NeverCalledBackend:
    """Asserts the backend.chat() is NEVER invoked. The short-circuit
    must short-circuit BEFORE making any LLM call."""

    def __init__(self) -> None:
        self.call_count = 0

    def chat(self, messages, **kw):  # type: ignore[no-untyped-def]
        self.call_count += 1
        raise AssertionError(
            "PaperImplementReviser short-circuit failed: backend.chat "
            "was called despite __tasks_md__ being missing. "
            "Short-circuit MUST happen before any LLM call."
        )


def test_short_circuit_when_tasks_md_missing(tmp_path: Path):
    backend = _NeverCalledBackend()
    reviser = PaperImplementReviser(
        backend=backend, repo_root=tmp_path, project_id="PROJ-TEST",
    )
    artifacts = {
        "projects/PROJ-TEST/paper/source/main.tex": "% paper content",
        # NOTE: no __tasks_md__ key
        "__paper_spec_md__": "# Paper spec\n",
        "__paper_plan_md__": "# Paper plan\n",
    }
    concerns = [
        Concern(
            id="C001", reviewer="claim_accuracy", severity=Severity.SCIENCE,
            artifact="paper/source/main.tex", location="",
            text="A fabricated citation appears in the manuscript.",
        ),
    ]
    updated, responses = reviser.revise(artifacts, concerns)
    # Backend was never called.
    assert backend.call_count == 0
    # Artifacts unchanged.
    assert updated == artifacts
    # One ConcernResponse per concern.
    assert len(responses) == 1
    assert responses[0].concern_id == "C001"
    assert "tasks.md" in responses[0].response.lower()
    assert responses[0].what_changed == "<no-op: tasks.md missing>"


def test_short_circuit_when_tasks_md_empty(tmp_path: Path):
    """An EMPTY ``__tasks_md__`` should also short-circuit (the
    dispatcher can't route through whitespace)."""
    backend = _NeverCalledBackend()
    reviser = PaperImplementReviser(
        backend=backend, repo_root=tmp_path, project_id="PROJ-TEST",
    )
    artifacts = {
        "projects/PROJ-TEST/paper/source/main.tex": "% paper",
        "__tasks_md__": "   \n   \n",  # whitespace only
    }
    concerns = [Concern(
        id="C001", reviewer="x", severity=Severity.WRITING,
        artifact="x", location="", text="x",
    )]
    _updated, responses = reviser.revise(artifacts, concerns)
    assert backend.call_count == 0
    assert len(responses) == 1


def test_short_circuit_handles_multiple_concerns(tmp_path: Path):
    """All concerns get a ConcernResponse, not just the first."""
    backend = _NeverCalledBackend()
    reviser = PaperImplementReviser(
        backend=backend, repo_root=tmp_path, project_id="PROJ-TEST",
    )
    artifacts = {
        "projects/PROJ-TEST/paper/source/main.tex": "% paper",
    }
    concerns = [
        Concern(id=f"C{i:03d}", reviewer="x", severity=Severity.WRITING,
                artifact="x", location="", text=f"concern {i}")
        for i in range(5)
    ]
    _, responses = reviser.revise(artifacts, concerns)
    assert len(responses) == 5
    assert {r.concern_id for r in responses} == {
        f"C{i:03d}" for i in range(5)
    }
