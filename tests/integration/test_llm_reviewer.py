"""Tests for the live LLMReviewer (spec 015 — unblocks T068 real-call
calibration).

Fake-backend tests verify:
- Prompt loading (lens prompt + SSoT shared block concatenated; missing
  file → RuntimeError).
- YAML-frontmatter parsing (missing frontmatter / invalid YAML / unknown
  severity all RuntimeError).
- identify() returns the structured Concerns from a valid response.
- rereview() pass/fail per prior concern based on whether the LLM
  reports them as still open.
- The engine round-trips a live LLMReviewer panel + a live Reviser
  end-to-end (no TODO placeholders involved).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from llmxive.convergence.llm_reviewer import (
    LLMReviewer,
    _parse_response,
    _prompt_path_for,
    build_panel,
    sha256_hex,
)
from llmxive.convergence.types import Concern, Severity

_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class _FakeResponse:
    text: str
    model: str = "fake-model"
    backend: str = "fake"


@dataclass
class _FakeBackend:
    responses: list[str]

    def chat(self, messages, model=None):  # type: ignore[no-untyped-def]
        if not self.responses:
            raise RuntimeError("out of canned responses")
        return _FakeResponse(text=self.responses.pop(0))


# --- prompt loading -------------------------------------------------------


def test_prompt_path_uses_stage_prefix_table():
    p = _prompt_path_for(
        stage="clarified", lens="requirements_coverage", repo_root=_REPO_ROOT,
    )
    assert p.name == "panel_spec_requirements_coverage.md"
    assert p.exists()


def test_prompt_path_honors_filename_overrides():
    p = _prompt_path_for(
        stage="planned", lens="plan_consistency", repo_root=_REPO_ROOT,
    )
    assert p.name == "panel_plan_consistency.md"
    assert p.exists()


def test_unknown_stage_raises_during_path_lookup():
    with pytest.raises(ValueError, match="unknown stage"):
        _prompt_path_for(stage="not_a_stage", lens="x", repo_root=_REPO_ROOT)


def test_llm_reviewer_constructor_loads_prompt():
    backend = _FakeBackend(responses=[])
    rev = LLMReviewer(
        lens="requirements_coverage", stage="clarified",
        backend=backend, repo_root=_REPO_ROOT,
    )
    # System prompt is the lens prompt + the shared block, concatenated.
    assert "requirements_coverage" in rev._system_prompt
    assert "Severity" in rev._system_prompt  # shared block header
    assert rev.name == "requirements_coverage"


def test_missing_prompt_raises_at_construction():
    backend = _FakeBackend(responses=[])
    with pytest.raises(RuntimeError, match="panel prompt not found"):
        LLMReviewer(
            lens="not_a_real_lens", stage="clarified",
            backend=backend, repo_root=_REPO_ROOT,
        )


# --- response parsing ----------------------------------------------------


_VALID_RESPONSE = """\
---
reviewer_name: requirements_coverage
reviewer_kind: llm
stage: clarified
artifact_path: specs/000-x/spec.md
artifact_hash: abc123
verdict: minor_revision
concerns:
  - severity: requirement
    location: "FR-002"
    text: "FR-002 has no corresponding success criterion"
---

The spec declares FR-002 but never ties it to a measurable outcome.
"""


def test_parse_response_extracts_one_concern():
    verdict, concerns = _parse_response(
        _VALID_RESPONSE, lens="requirements_coverage",
        stage="clarified", default_artifact="specs/000-x/spec.md",
    )
    assert verdict == "minor_revision"
    assert len(concerns) == 1
    c = concerns[0]
    assert c.severity == Severity.REQUIREMENT
    assert c.reviewer == "requirements_coverage"
    assert "FR-002" in c.text


def test_parse_response_missing_frontmatter_raises():
    with pytest.raises(RuntimeError, match="no YAML frontmatter"):
        _parse_response(
            "Just prose, no YAML.",
            lens="x", stage="y", default_artifact="z",
        )


def test_parse_response_invalid_yaml_raises():
    bad = "---\nverdict: [unclosed list\n---\nprose"
    with pytest.raises(RuntimeError, match="not valid YAML"):
        _parse_response(bad, lens="x", stage="y", default_artifact="z")


def test_parse_response_unknown_severity_raises():
    bad = (
        "---\n"
        "verdict: minor_revision\n"
        "concerns:\n"
        "  - severity: totally_made_up\n"
        "    text: x\n"
        "---\nprose"
    )
    with pytest.raises(RuntimeError, match="unknown severity"):
        _parse_response(bad, lens="x", stage="y", default_artifact="z")


def test_parse_response_no_concerns_is_accept():
    minimal = "---\nverdict: accept\n---\nLooks good.\n"
    verdict, concerns = _parse_response(
        minimal, lens="x", stage="y", default_artifact="z",
    )
    assert verdict == "accept"
    assert concerns == []


# --- identify() end-to-end -----------------------------------------------


def test_identify_returns_parsed_concerns():
    backend = _FakeBackend(responses=[_VALID_RESPONSE])
    rev = LLMReviewer(
        lens="requirements_coverage", stage="clarified",
        backend=backend, repo_root=_REPO_ROOT,
    )
    artifacts = {"specs/000-x/spec.md": "# spec\n- FR-002: do Y\n"}
    concerns = rev.identify(artifacts, constitution=None, advisory=[])
    assert len(concerns) == 1
    assert concerns[0].text.startswith("FR-002")


# --- rereview() end-to-end -----------------------------------------------


def test_rereview_passes_concern_when_not_in_new_concerns():
    """Prior concern with id C1 — LLM emits NO concerns → C1 passes."""
    response = "---\nverdict: accept\n---\nAll good now.\n"
    backend = _FakeBackend(responses=[response])
    rev = LLMReviewer(
        lens="requirements_coverage", stage="clarified",
        backend=backend, repo_root=_REPO_ROOT,
    )
    prior = [Concern(
        id="C1", reviewer="requirements_coverage", severity=Severity.REQUIREMENT,
        artifact="specs/000-x/spec.md", location="FR-002", text="orphan FR",
    )]
    verdicts = rev.rereview(
        {"specs/000-x/spec.md": "# revised spec"},
        own_concerns=prior, responses=[],
        constitution=None, advisory=[],
    )
    assert len(verdicts) == 1
    assert verdicts[0].concern_id == "C1"
    assert verdicts[0].status == "pass"


def test_rereview_fails_concern_when_still_present():
    """LLM re-flags C1 with the same id → C1 fails."""
    response = (
        "---\n"
        "verdict: minor_revision\n"
        "concerns:\n"
        "  - id: C1\n"
        "    severity: requirement\n"
        "    location: FR-002\n"
        "    text: still orphaned\n"
        "---\nprose"
    )
    backend = _FakeBackend(responses=[response])
    rev = LLMReviewer(
        lens="requirements_coverage", stage="clarified",
        backend=backend, repo_root=_REPO_ROOT,
    )
    prior = [Concern(
        id="C1", reviewer="requirements_coverage", severity=Severity.REQUIREMENT,
        artifact="specs/000-x/spec.md", location="FR-002", text="orphan FR",
    )]
    verdicts = rev.rereview(
        {"specs/000-x/spec.md": "# revised spec"},
        own_concerns=prior, responses=[],
        constitution=None, advisory=[],
    )
    assert verdicts[0].status == "fail"


# --- helpers --------------------------------------------------------------


def test_sha256_hex_is_stable():
    assert sha256_hex("hello") == sha256_hex("hello")
    assert sha256_hex("hello") != sha256_hex("world")
    assert len(sha256_hex("anything")) == 64


def test_build_panel_creates_one_reviewer_per_lens():
    backend = _FakeBackend(responses=[])
    panel = build_panel(
        stage="clarified",
        lenses=["requirements_coverage", "internal_consistency", "testability", "scope"],
        backend=backend, repo_root=_REPO_ROOT,
    )
    assert len(panel) == 4
    assert {r.name for r in panel} == {
        "requirements_coverage", "internal_consistency", "testability", "scope",
    }
    # Every reviewer has its system prompt loaded.
    for r in panel:
        assert "Severity" in r._system_prompt


# --- end-to-end with engine ----------------------------------------------


def test_live_panel_drives_engine_to_convergence():
    """Full integration: LLMReviewer panel + SpecReviser + engine —
    no TODO placeholders involved. The fake backend returns a clean
    'accept' R1 response per reviewer (4 reviewers in the spec panel).
    Engine converges immediately at R1 (no R2/R3 cycle needed)."""
    from llmxive.convergence.engine import run_convergence
    from llmxive.convergence.reviewspecs import build_spec_reviewspec

    accept_response = "---\nverdict: accept\n---\nLooks clean.\n"
    backend = _FakeBackend(responses=[accept_response] * 10)
    spec = build_spec_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    # Wire 4 LIVE reviewers (replaces the registry's TodoReviewer
    # placeholders).
    spec.reviewers = build_panel(
        stage="clarified",
        lenses=["requirements_coverage", "internal_consistency",
                "testability", "scope"],
        backend=backend, repo_root=_REPO_ROOT,
    )
    artifacts = {"specs/000-x/spec.md": "# spec\nFR-001: do X.\nSC-001: tests pass.\n"}
    result = run_convergence(spec, artifacts)
    assert result.converged is True
    assert result.next_stage == "planned"
