"""Spec 020 T006 — planning stage skips low-level verification (C2/C8; FR-002/003).

Offline. The planning branch of ``process_document`` must, for a low-level claim:
NOT resolve / fetch / ground it, NOT emit an ``[UNRESOLVED-CLAIM:]`` marker, NOT
block the gate — and instead strip/smooth the specific value out. We inject a
known claim through the (separately tested) ``extract_claims`` collaborator and
assert ``resolve`` is never reached; the real extraction + rewrite are covered by
the real-call integration test (T007).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from llmxive.backends.base import ChatResponse
from llmxive.claims import service as svc
from llmxive.claims.gate import CLAIM_MARKER_PREFIX
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id

PASSAGE = "There are exactly 49 prime knots at 13 crossings (Rolfsen 1976)."
DOC = f"# Plan\n\n{PASSAGE}\n\nThe method enumerates knots up to isotopy.\n"


@dataclass
class _Backend:
    reply: str = "The count of prime knots grows with crossing number (Rolfsen 1976)."
    name: str = "dartmouth"
    calls: list[Any] = field(default_factory=list)

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
        self.calls.append(model)
        return ChatResponse(text=self.reply, model=model or "m", backend=self.name)


def _lowlevel_claim() -> Claim:
    return Claim(
        claim_id=compute_claim_id(ClaimKind.NUMERIC, PASSAGE, ""),
        kind=ClaimKind.NUMERIC,
        raw_text=PASSAGE,
        canonical=PASSAGE,
        context="",
        artifact_path="projects/PROJ-x/specs/plan.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="",
    )


@pytest.fixture
def _patched(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(svc, "extract_claims", lambda *a, **k: [_lowlevel_claim()])

    def _boom(*a: Any, **k: Any) -> Any:  # resolve MUST NOT be called in planning
        raise AssertionError("resolve() called in a planning stage (FR-002 violation)")

    monkeypatch.setattr(svc, "resolve", _boom)


@pytest.mark.parametrize("stage", ["spec", "plan", "tasks"])
def test_planning_strips_lowlevel_no_marker_no_block(
    stage: str, _patched: None, tmp_path: Path
) -> None:
    out, claims, report = svc.process_document(
        DOC,
        artifact_path="projects/PROJ-x/specs/plan.md",
        project_id="PROJ-x",
        backend=_Backend(),
        model=None,
        repo_root=tmp_path,
        stage_label=stage,
    )
    assert "49" not in out                       # specific value removed (FR-002a)
    assert CLAIM_MARKER_PREFIX not in out        # no [UNRESOLVED-CLAIM:] (FR-003)
    assert report.blocked is False               # planning never blocks on low-level
    assert claims == []                          # nothing registered/resolved
    assert "Rolfsen 1976" in out                 # citation preserved (FR-002c)
    assert "method enumerates knots" in out      # non-claim content preserved


def test_fill_boundary_gate_planning(tmp_path: Path) -> None:
    # T011 defense-in-depth: channels_for + fill_claim short-circuit a low-level
    # claim in a planning stage with NO fetch, while a non-planning label is unaffected.
    from llmxive.fill.channels import channels_for
    from llmxive.fill.service import fill_claim

    assert channels_for(ClaimKind.NUMERIC, math=False, stage_label="plan") == []
    assert channels_for(ClaimKind.ENTITY_FACT, math=False, stage_label="spec") == []
    # non-planning labels keep the normal channel list
    assert channels_for(ClaimKind.NUMERIC, math=False, stage_label="paper_plan")
    assert channels_for(ClaimKind.NUMERIC, math=False, stage_label=None)

    res = fill_claim(_lowlevel_claim(), backend=None, model=None,
                     repo_root=tmp_path, stage_label="plan")
    assert res.status == "blocked"
    assert "planning stage" in (res.reason or "")


def test_full_stage_still_resolves(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # A non-planning (paper/None) stage must NOT take the planning branch — it
    # reaches resolve() as before (here proven by the boom-on-resolve guard firing).
    monkeypatch.setattr(svc, "extract_claims", lambda *a, **k: [_lowlevel_claim()])

    def _boom(*a: Any, **k: Any) -> Any:
        raise AssertionError("resolve reached")  # expected in full stage

    monkeypatch.setattr(svc, "resolve", _boom)
    with pytest.raises(AssertionError, match="resolve reached"):
        # process_document swallows extraction errors but NOT a resolve AssertionError
        # raised inside resolve_registered_claims → it propagates, proving the full
        # path runs resolve() while planning does not.
        svc.process_document(
            DOC, artifact_path="projects/PROJ-x/specs/plan.md", project_id="PROJ-x",
            backend=_Backend(), model=None, repo_root=tmp_path, stage_label="paper_plan",
        )
