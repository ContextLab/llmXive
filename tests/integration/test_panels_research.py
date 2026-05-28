"""Research-side panel integration tests (spec 015 T046).

Exercises the full convergence cycle (engine + live Reviser + fake panel
of reviewers) end-to-end for every research-side reviewable stage:

- idea (`flesh_out_complete`) — covered indirectly by spec stage (idea
  uses placeholder TODO reviewers + reviser until T021 + T040 wires
  flesh_out as a live reviser; the build_*_reviewspec for idea isn't
  yet exposed because the idea-flesh-out agent isn't yet wrapped as a
  Reviser).
- spec (`clarified`) — SpecReviser + 4-lens spec panel.
- plan (`planned`) — PlanReviser + 4-lens plan panel.
- tasks (`tasked`) — TasksReviser + 4-lens tasks panel.
- research_unit (`research_review`) — ImplementerReviser + 8-panel.

Each test uses a FAKE backend for the reviser's LLM call (deterministic
JSON) and HAND-ROLLED reviewer objects implementing the Reviewer
Protocol. This validates the engine ↔ reviser ↔ panel handshake without
requiring real LLM calls. Real-call variants (with the Dartmouth
qwen3.5-122b model) live in ``tests/real_call/``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from llmxive.convergence.engine import run_convergence
from llmxive.convergence.reviewspecs import (
    build_idea_reviewspec,
    build_implement_reviewspec,
    build_plan_reviewspec,
    build_spec_reviewspec,
    build_tasks_reviewspec,
)
from llmxive.convergence.types import Concern, Severity, Verdict

_REPO_ROOT = Path(__file__).resolve().parents[2]


# --- Test doubles ---------------------------------------------------------


@dataclass
class _FakeResponse:
    text: str
    model: str = "fake-model"
    backend: str = "fake"


@dataclass
class _FakeBackend:
    """Backend stand-in: serves the next response from a queue."""

    responses: list[str]

    def chat(self, messages, model=None):  # type: ignore[no-untyped-def]
        if not self.responses:
            raise RuntimeError("_FakeBackend ran out of canned responses")
        return _FakeResponse(text=self.responses.pop(0))


class _ScriptedReviewer:
    """Hand-rolled Reviewer-Protocol-conformant fake.

    Each call to ``identify`` returns the configured ``initial_concerns``;
    each ``rereview`` accepts every concern whose id appears in
    ``accepts_round_<n>``. Tracks calls so tests can assert ordering."""

    def __init__(
        self,
        name: str,
        *,
        initial_concerns: list[Concern],
        accepts_per_round: dict[int, list[str]],
    ) -> None:
        self.name = name
        self._initial = initial_concerns
        self._accepts = accepts_per_round
        self._rereview_round = 0
        self.identify_calls = 0
        self.rereview_calls = 0

    def identify(self, artifacts, *, constitution, advisory):  # type: ignore[no-untyped-def]
        self.identify_calls += 1
        return list(self._initial)

    def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):  # type: ignore[no-untyped-def]
        self.rereview_calls += 1
        self._rereview_round += 1
        accept_ids = self._accepts.get(self._rereview_round, [])
        verdicts: list[Verdict] = []
        for c in own_concerns:
            status = "pass" if c.id in accept_ids else "fail"
            verdicts.append(
                Verdict(concern_id=c.id, reviewer=self.name, status=status)
            )
        return verdicts


def _replace_panel(spec, reviewers):  # type: ignore[no-untyped-def]
    """Swap the registry's TODO reviewers for the test's scripted ones.
    Returns the original spec mutated in place (the engine reads
    spec.reviewers, so this is the simplest wiring)."""
    spec.reviewers = list(reviewers)
    return spec


# --- Idea stage end-to-end ------------------------------------------------


def test_idea_panel_runs_end_to_end_through_engine(tmp_path: Path):
    """FleshOutReviser + a 1-lens panel (rq_validity) that raises one
    concern then accepts in R3 → ``converged=True`` at round 1; the
    engine advances to ``validated`` (the idea convergence unit's
    ``advance_stage``)."""
    idea_key = "projects/PROJ-000-test/idea/an-idea.md"
    artifacts = {
        idea_key: (
            "# An idea\n## Research question\nDoes X cause Y?\n"
            "## Methodology sketch\n- Use data\n"
        ),
    }
    concern = Concern(
        id="I1", reviewer="rq_validity", severity=Severity.METHODOLOGY,
        artifact=idea_key, location="Research question",
        text="research question reads as method-grounded — needs phenomenon framing",
    )
    reviewer = _ScriptedReviewer(
        "rq_validity",
        initial_concerns=[concern],
        accepts_per_round={1: ["I1"]},
    )
    fake_reply = json.dumps({
        "new_idea_md": (
            "# An idea\n## Research question\n"
            "Does X (measured channel A) predict Y (channel B)?\n"
            "## Methodology sketch\n- Use https://uci.example.org/dataset.csv\n"
        ),
        "responses": [
            {"concern_id": "I1", "response": "Reframed phenomenologically",
             "what_changed": "RQ now names independent channels",
             "artifacts_changed": [idea_key]},
        ],
    })
    backend = _FakeBackend(responses=[fake_reply])
    spec = build_idea_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    _replace_panel(spec, [reviewer])
    result = run_convergence(spec, artifacts)

    assert result.converged is True
    assert result.rounds_used == 1
    assert result.next_stage == "validated"
    assert any(c.id == "I1" for c in result.concern_history)
    assert any(r.concern_id == "I1" for r in result.response_history)


def test_idea_panel_kickbacks_route_to_brainstormed(tmp_path: Path):
    """Idea panel that NEVER accepts → cap-hit → ``converged=False`` with
    a ``KickbackRecord`` routed to ``brainstormed`` (the idea stage's only
    upstream stage; FATAL-class concerns flow back to a different idea)."""
    idea_key = "projects/PROJ-000-test/idea/an-idea.md"
    artifacts = {idea_key: "# An idea\nresearch question: trivial.\n"}
    concern = Concern(
        id="I1", reviewer="idea_quality", severity=Severity.SCIENCE,
        artifact=idea_key, location="",
        text="idea is fundamentally unsalvageable",
    )
    reviewer = _ScriptedReviewer(
        "idea_quality",
        initial_concerns=[concern],
        accepts_per_round={},  # never accepts
    )
    fake_reply = json.dumps({
        "new_idea_md": "# An idea v_n\n",
        "responses": [{"concern_id": "I1", "response": "tried", "what_changed": "edited"}],
    })
    backend = _FakeBackend(responses=[fake_reply] * 5)
    spec = build_idea_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    _replace_panel(spec, [reviewer])
    result = run_convergence(spec, artifacts)

    assert result.converged is False
    assert result.rounds_used == spec.max_rounds
    assert result.kickback is not None
    # Every severity at the idea stage routes back to brainstormed (the
    # only prior stage).
    assert result.kickback.to_stage == "brainstormed"
    assert result.kickback.worst_severity == Severity.SCIENCE


# --- Spec stage end-to-end ------------------------------------------------


def test_spec_convergence_accepts_after_one_revision(tmp_path: Path):
    """SpecReviser + a 1-lens panel that raises one concern then accepts
    in R3 → ``converged=True`` at round 1."""
    spec_key = "specs/000-x/spec.md"
    artifacts = {
        spec_key: (
            "# spec v1\n## FR\n- FR-001: implement X "
            "[NEEDS CLARIFICATION: which X?].\n"
        ),
        "idea/x.md": "# idea\nResearch question: does X cause Y?",
    }
    concern = Concern(
        id="C1", reviewer="requirements_coverage", severity=Severity.REQUIREMENT,
        artifact=spec_key, location="FR-001", text="resolve the X clarification marker",
    )
    reviewer = _ScriptedReviewer(
        "requirements_coverage",
        initial_concerns=[concern],
        accepts_per_round={1: ["C1"]},  # accepts on first re-review
    )
    fake_reply = json.dumps({
        "new_spec_md": (
            "# spec v2\n## FR\n- FR-001: implement X (the metric AUC).\n"
        ),
        "responses": [
            {"concern_id": "C1", "response": "Resolved", "what_changed": "FR-001 names AUC",
             "artifacts_changed": [spec_key]},
        ],
    })
    backend = _FakeBackend(responses=[fake_reply])
    spec = build_spec_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    _replace_panel(spec, [reviewer])
    result = run_convergence(spec, artifacts)

    assert result.converged is True
    assert result.rounds_used == 1
    assert result.next_stage == "planned"
    assert any(c.id == "C1" for c in result.concern_history)
    assert any(r.concern_id == "C1" for r in result.response_history)


def test_spec_convergence_kickbacks_when_panel_never_accepts(tmp_path: Path):
    """SpecReviser + a panel that NEVER accepts → cap-hit → ``converged=False``
    with a ``KickbackRecord`` routed by worst severity."""
    spec_key = "specs/000-x/spec.md"
    artifacts = {spec_key: "# spec\n"}
    concern = Concern(
        id="C1", reviewer="scope", severity=Severity.SCIENCE,
        artifact=spec_key, location="", text="research question is unsalvageable",
    )
    reviewer = _ScriptedReviewer(
        "scope",
        initial_concerns=[concern],
        accepts_per_round={},  # never accepts
    )
    # Need one canned response per round (3 by default).
    fake_reply = json.dumps({
        "new_spec_md": "# spec v_n",
        "responses": [{"concern_id": "C1", "response": "tried", "what_changed": "edited"}],
    })
    backend = _FakeBackend(responses=[fake_reply] * 5)
    spec = build_spec_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    _replace_panel(spec, [reviewer])
    result = run_convergence(spec, artifacts)

    assert result.converged is False
    assert result.rounds_used == spec.max_rounds  # hit the cap
    assert result.kickback is not None
    # Science-class kickback routes to flesh_out_in_progress per the
    # registry's kickback_routing for the clarified stage.
    assert result.kickback.to_stage == "flesh_out_in_progress"
    assert result.kickback.worst_severity == Severity.SCIENCE


# --- Plan stage end-to-end -----------------------------------------------


def test_plan_convergence_accepts_after_one_revision(tmp_path: Path):
    plan_key = "specs/000-x/plan.md"
    data_model_key = "specs/000-x/data-model.md"
    artifacts = {
        plan_key: "# plan v1\nMethodology: regression.\n",
        data_model_key: "# data-model v1\nentity: trial\n",
        "specs/000-x/spec.md": "# spec\n- FR-001: X\n",
    }
    concern = Concern(
        id="P1", reviewer="methodology", severity=Severity.METHODOLOGY,
        artifact=plan_key, location="Methodology",
        text="regression alone doesn't establish causality",
    )
    reviewer = _ScriptedReviewer(
        "methodology",
        initial_concerns=[concern],
        accepts_per_round={1: ["P1"]},
    )
    fake_reply = json.dumps({
        "updated_artifacts": {plan_key: "# plan v2\nMethodology: regression + RCT.\n"},
        "responses": [
            {"concern_id": "P1", "response": "Added RCT", "what_changed": "now includes RCT",
             "artifacts_changed": [plan_key]},
        ],
    })
    backend = _FakeBackend(responses=[fake_reply])
    spec = build_plan_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    _replace_panel(spec, [reviewer])
    result = run_convergence(spec, artifacts)

    assert result.converged is True
    assert result.next_stage == "tasked"


# --- Tasks stage end-to-end ----------------------------------------------


def test_tasks_convergence_two_round_resolution(tmp_path: Path):
    """TasksReviser + a reviewer that fails round 1 but accepts round 2
    → ``converged=True`` at round 2 (proves the engine actually loops)."""
    tasks_key = "specs/000-x/tasks.md"
    artifacts = {
        tasks_key: "# tasks v1\n- T001 do X\n",
        "specs/000-x/spec.md": "# spec\n- FR-001: X\n- FR-002: Y\n",
        "specs/000-x/plan.md": "# plan",
    }
    concern = Concern(
        id="T1", reviewer="coverage", severity=Severity.REQUIREMENT,
        artifact=tasks_key, location="FR-002", text="FR-002 has no task",
    )
    reviewer = _ScriptedReviewer(
        "coverage",
        initial_concerns=[concern],
        accepts_per_round={2: ["T1"]},  # accepts only on round 2
    )
    # Round 1 reply (insufficient) + round 2 reply (sufficient).
    round1 = json.dumps({
        "new_tasks_md": "# tasks v2\n- T001 do X\n",  # didn't actually add T002
        "responses": [{"concern_id": "T1", "response": "tried", "what_changed": "tried"}],
    })
    round2 = json.dumps({
        "new_tasks_md": "# tasks v3\n- T001 do X\n- T002 do Y\n",
        "responses": [{"concern_id": "T1", "response": "added T002", "what_changed": "T002 added"}],
    })
    backend = _FakeBackend(responses=[round1, round2])
    spec = build_tasks_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    _replace_panel(spec, [reviewer])
    result = run_convergence(spec, artifacts)

    assert result.converged is True
    assert result.rounds_used == 2
    assert reviewer.rereview_calls == 2  # the engine looped


# --- Research-unit (implement) stage end-to-end --------------------------


def test_implement_convergence_filesystem_unverified_surfaces(tmp_path: Path):
    """ImplementerReviser + a reviewer that accepts the code change BUT
    a `[X]` task names a file the reviser didn't create → the
    `<filesystem-unverified:T###>` synthetic response shows up in the
    engine's response history (R3 sees the post-revise failure)."""
    code_key = "src/proj/x.py"
    # Create the file that T001 claims, but T002's claim won't be met
    # because the reviser doesn't actually create the new file.
    (tmp_path / "src" / "proj").mkdir(parents=True)
    (tmp_path / "src" / "proj" / "x.py").write_text("# existing")
    artifacts = {
        code_key: "# existing",
        "__tasks_md__": (
            "- [X] T001 wrote `src/proj/x.py`\n"
            "- [X] T002 wrote `src/proj/missing.py`\n"
        ),
    }
    # The reviewer raises one concern, accepts on R3.
    concern = Concern(
        id="CC1", reviewer="code_quality", severity=Severity.CODE,
        artifact=code_key, location="", text="add a docstring",
    )
    reviewer = _ScriptedReviewer(
        "code_quality",
        initial_concerns=[concern],
        accepts_per_round={1: ["CC1"]},
    )
    fake_reply = json.dumps({
        "updated_artifacts": {code_key: '"""docstring."""\n# existing'},
        "responses": [{"concern_id": "CC1", "response": "added docstring",
                       "what_changed": "x.py now has docstring",
                       "artifacts_changed": [code_key]}],
    })
    backend = _FakeBackend(responses=[fake_reply])
    spec = build_implement_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
        project_root=tmp_path,
    )
    _replace_panel(spec, [reviewer])
    result = run_convergence(spec, artifacts)

    # The CC1 concern resolved, BUT the response history must also include
    # the synthetic <filesystem-unverified:T002> entry (closes #49).
    unverified = [r for r in result.response_history
                  if r.concern_id.startswith("<filesystem-unverified:")]
    assert len(unverified) >= 1
    assert any("T002" in r.concern_id for r in unverified)


# --- Producer-attribution: self-review prevention ------------------------


def test_self_review_prevention_excludes_producer(tmp_path: Path):
    """When ``producer`` is passed to ``run_convergence``, reviewers whose
    name matches MUST be excluded from the panel — closes the
    self-review-prevention loop (FR-018 / spec-015 T025)."""
    spec_key = "specs/000-x/spec.md"
    artifacts = {spec_key: "# spec\n"}
    # The producer was specifier+clarifier (which is also the reviser
    # name — no exclusion happens at the reviewer level). Set producer
    # = the reviewer name to verify exclusion.
    producer_reviewer = _ScriptedReviewer(
        "requirements_coverage",
        initial_concerns=[Concern(id="X1", reviewer="requirements_coverage",
                                   severity=Severity.WRITING, artifact=spec_key,
                                   location="", text="x")],
        accepts_per_round={},
    )
    other_reviewer = _ScriptedReviewer(
        "scope",
        initial_concerns=[],  # accepts at R1 immediately
        accepts_per_round={},
    )
    backend = _FakeBackend(responses=[])  # no reviser calls expected
    spec = build_spec_reviewspec(
        backend=backend, repo_root=_REPO_ROOT, project_id="PROJ-000-test",
    )
    _replace_panel(spec, [producer_reviewer, other_reviewer])
    result = run_convergence(spec, artifacts, producer="requirements_coverage")

    # The producer reviewer was excluded → no concerns raised → converged.
    assert result.converged is True
    assert producer_reviewer.identify_calls == 0
    assert other_reviewer.identify_calls == 1


def test_exempt_stage_raises_when_run_convergence_called():
    """Engine misuse: trying to run convergence on an EXEMPT stage
    (paper_initializer, status_reporter, etc.) MUST raise rather than
    silently no-op."""
    from llmxive.convergence.types import ReviewSpec

    fake_spec = ReviewSpec(
        stage="paper_initializer",
        artifacts=[],
        reviewers=[],
        reviser=None,
        kickback_routing={},
        overflow_goal="",
        exempt=True,
    )
    with pytest.raises(ValueError, match="is EXEMPT"):
        run_convergence(fake_spec, {})
