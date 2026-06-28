"""Regression (spec 023 defect #12 + issue #355): a malformed reviser reply
must not kill the panel run.

* spec 023 defect #12 — observed live on PROJ-552's plan panel, where a
  single parse-to-zero LLM reply aborted hours of converged review rounds as
  a generic engine failure. The engine retries ``revise()`` once on a
  recoverable RuntimeError.
* issue #355 — observed live on PROJ-167's plan panel: under a heavy concern
  load the reviser model PERSISTENTLY spent its whole output budget on the
  per-concern change-log and never emitted the revised artifact (a ```json
  ``{"responses": [...]}``-only reply, often truncated). Every retry layer
  raised the same malformed-reply RuntimeError and the panel crashed + filed
  an engine-failure issue. A persistently malformed reply that survives the
  retries is simply "no artifact change this round": the engine now degrades
  to an empty revision and lets the bounded loop carry the open concerns to
  the next round / adaptive kickback — it NEVER fabricates an artifact, and a
  genuine engine defect (any non-malformed RuntimeError) still surfaces.

Backend outages keep the clean-abort path untouched.

Uses the established offline-engine fixture pattern (scripted reviewers/
revisers implementing the real protocol — not mocks of the engine)."""

from __future__ import annotations

from pathlib import Path

import pytest

from llmxive.backends.base import BackendUnavailable
from llmxive.convergence.types import (
    Concern,
    ConcernResponse,
    ReviewSpec,
    Severity,
)
from llmxive.speckit._stage_panel import run_stage_panel

KEY = "projects/PROJ-940-x/specs/001-x/spec.md"


class _AcceptingReviewer:
    name = "methodology"

    def identify(self, artifacts, *, constitution, advisory):
        return [
            Concern(
                id="c1", reviewer="methodology", severity=Severity.SCIENCE,
                artifact=KEY, text="tighten the method",
            )
        ]

    def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):
        from llmxive.convergence.types import Verdict

        return [
            Verdict(concern_id=c.id, reviewer=self.name, status="pass")
            for c in own_concerns
        ]


class _FlakyThenGoodReviser:
    """First revise() raises the live parse-to-zero error; the retry works."""

    name = "flaky"

    def __init__(self) -> None:
        self.calls = 0

    def revise(self, artifacts, concerns):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError(
                "PlanReviser: response JSON has no usable "
                "'updated_artifacts' map; got: 0 artifacts"
            )
        responses = [
            ConcernResponse(
                concern_id=c.id, response="addressed", what_changed="edit",
                artifacts_changed=[KEY],
            )
            for c in concerns
        ]
        return {KEY: artifacts.get(KEY, "") + "\nrevised"}, responses


class _AlwaysOutageReviser:
    name = "down"

    def revise(self, artifacts, concerns):
        raise BackendUnavailable("endpoint down")


def _spec(reviser) -> ReviewSpec:
    return ReviewSpec(
        stage="clarified",
        artifacts=[KEY],
        reviewers=[_AcceptingReviewer()],
        reviser=reviser,
        kickback_routing={
            Severity.WRITING: "project_initialized",
            Severity.SCIENCE: "flesh_out_in_progress",
            Severity.FATAL: "flesh_out_in_progress",
        },
        overflow_goal="preserve requirements",
        advance_stage="clarified",
        max_rounds=3,
    )


def _run(tmp_path: Path, reviser):
    repo = tmp_path / "repo"
    feature = repo / "projects" / "PROJ-940-x" / "specs" / "001-x"
    feature.mkdir(parents=True)
    spec_md = feature / "spec.md"
    spec_md.write_text("# spec\n- **FR-001**: do X\n", encoding="utf-8")
    memory_dir = repo / "projects" / "PROJ-940-x" / ".specify" / "memory"
    return run_stage_panel(
        stage_label="spec",
        spec=_spec(reviser),
        artifact_paths={KEY: spec_md},
        extra_inputs={
            "__idea_md__": "idea body",
            "__comments_block__": "",
            "__spec_template__": "template",
        },
        repo_root=repo,
        memory_dir=memory_dir,
        producer=None,
    )


def test_one_malformed_reply_is_retried_and_panel_converges(tmp_path: Path) -> None:
    reviser = _FlakyThenGoodReviser()
    _run(tmp_path, reviser)  # converges: accepter passes after the retried revise
    assert reviser.calls == 2, "exactly one retry"


def test_genuine_engine_defect_still_fails_loudly(tmp_path: Path) -> None:
    """A persistent RuntimeError WITHOUT the malformed-reply signature is a
    genuine engine defect — it must surface (escalation + issue), never be
    silently absorbed as 'no artifact change'."""
    class _AlwaysBuggy(_FlakyThenGoodReviser):
        def revise(self, artifacts, concerns):
            self.calls += 1
            raise RuntimeError("KeyError: 'unexpected' — a real engine bug")

    from llmxive.speckit._stage_panel import StagePanelEscalation
    from llmxive.state import escalations as esc_mod

    reviser = _AlwaysBuggy()
    import unittest.mock as _m
    with _m.patch.object(esc_mod, "file_engine_failure_issue", lambda **kw: 1):
        with pytest.raises(StagePanelEscalation):
            _run(tmp_path, reviser)
    assert reviser.calls == 2, "bounded — one retry, then propagate"


class _PersistentMalformedReviser:
    """Issue #355: every revise() raises the malformed-reply RuntimeError that
    the ```json ``{"responses": [...]}``-only / truncated-change-log reply
    produces (the message carries the 'no usable' / 'parseable' signature)."""

    name = "malformed"

    def __init__(self) -> None:
        self.calls = 0

    def revise(self, artifacts, concerns):
        self.calls += 1
        raise RuntimeError(
            "PlanReviser: backend did not return parseable JSON: reviser "
            "response carried neither '===BEGIN_ARTIFACT' markers nor "
            "parseable legacy JSON; first 200 chars: '```json\\n{\"responses\"'"
        )


class _DissentUntilArtifactChanges:
    """Re-review passes ONLY when the artifact body actually changed this
    round — so a 'no artifact change' degradation keeps the concern OPEN and
    drives the bounded loop to its cap → adaptive kickback (not a crash)."""

    name = "methodology"

    def identify(self, artifacts, *, constitution, advisory):
        return [
            Concern(
                id="c1", reviewer="methodology", severity=Severity.SCIENCE,
                artifact=KEY, text="tighten the method",
            )
        ]

    def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):
        from llmxive.convergence.types import Verdict

        changed = "revised" in (artifacts.get(KEY) or "")
        return [
            Verdict(
                concern_id=c.id, reviewer=self.name,
                status="pass" if changed else "fail",
            )
            for c in own_concerns
        ]


def test_issue355_persistent_malformed_reply_degrades_to_kickback(
    tmp_path: Path,
) -> None:
    """Issue #355: a reviser that PERSISTENTLY returns a malformed (no-artifact)
    reply must NOT crash the panel as an engine failure. It degrades to 'no
    artifact change this round'; the open concern carries forward to the cap →
    adaptive kickback (StagePanelKickback), and NO engine-failure issue is
    filed."""
    from llmxive.speckit import _stage_panel as sp
    from llmxive.speckit._stage_panel import (
        StagePanelEscalation,
        StagePanelKickback,
    )
    from llmxive.state import escalations as esc_mod

    spec = ReviewSpec(
        stage="clarified",
        artifacts=[KEY],
        reviewers=[_DissentUntilArtifactChanges()],
        reviser=_PersistentMalformedReviser(),
        kickback_routing={
            Severity.WRITING: "project_initialized",
            Severity.SCIENCE: "flesh_out_in_progress",
            Severity.FATAL: "flesh_out_in_progress",
        },
        overflow_goal="preserve requirements",
        advance_stage="clarified",
        max_rounds=3,
    )

    repo = tmp_path / "repo"
    feature = repo / "projects" / "PROJ-940-x" / "specs" / "001-x"
    feature.mkdir(parents=True)
    spec_md = feature / "spec.md"
    spec_md.write_text("# spec\n- **FR-001**: do X\n", encoding="utf-8")
    memory_dir = repo / "projects" / "PROJ-940-x" / ".specify" / "memory"

    import unittest.mock as _m

    filed: list[dict] = []

    def _record_issue(**kw):
        filed.append(kw)
        return 1

    with _m.patch.object(esc_mod, "file_engine_failure_issue", _record_issue):
        with pytest.raises(StagePanelKickback):
            sp.run_stage_panel(
                stage_label="spec",
                spec=spec,
                artifact_paths={KEY: spec_md},
                extra_inputs={
                    "__idea_md__": "idea body",
                    "__comments_block__": "",
                    "__spec_template__": "template",
                },
                repo_root=repo,
                memory_dir=memory_dir,
                producer=None,
            )
    assert not filed, "issue #355 degradation must NOT file an engine-failure issue"
    # Sanity: a kickback is NOT an escalation (engine-failure) path.
    assert not issubclass(StagePanelKickback, StagePanelEscalation)


def test_backend_outage_is_never_retried(tmp_path: Path) -> None:
    with pytest.raises(BackendUnavailable):
        _run(tmp_path, _AlwaysOutageReviser())
