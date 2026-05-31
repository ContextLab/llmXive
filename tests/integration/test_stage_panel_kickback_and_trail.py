"""``run_stage_panel`` sentinel + inspection-trail tests (F-14 / F-20 Part B).

Proves, against a constructed (non-mocked) ReviewSpec driven by scripted
reviewers + a fake reviser (the established offline-engine fixture pattern):

* a panel NON-CONVERGENCE writes ``convergence_kickback.yaml`` (with to_stage /
  reason / unresolved_concerns) and NOT ``human_input_needed.yaml``;
* a genuine engine EXCEPTION still writes ``human_input_needed.yaml``;
* a multi-round convergence persists a ``convergence_trail/<stage>-NNN.jsonl``
  provenance file with one JSON line per round.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from llmxive.backends.base import TransientBackendError
from llmxive.convergence.types import (
    Concern,
    ConcernResponse,
    ReviewSpec,
    Severity,
    Verdict,
)
from llmxive.speckit._stage_panel import (
    StagePanelEscalation,
    StagePanelKickback,
    run_stage_panel,
)

# --- Scripted reviewer / reviser (real protocol impls, not mocks) ---------


class _ScriptedReviewer:
    def __init__(self, name: str, concern: Concern, *, accept_round: int | None) -> None:
        self.name = name
        self._concern = concern
        self._accept_round = accept_round
        self._round = 0

    def identify(self, artifacts, *, constitution, advisory):  # type: ignore[no-untyped-def]
        return [self._concern]

    def rereview(self, artifacts, own_concerns, responses, *, constitution, advisory):  # type: ignore[no-untyped-def]
        self._round += 1
        status = "pass" if self._round == self._accept_round else "fail"
        return [
            Verdict(concern_id=c.id, reviewer=self.name, status=status)
            for c in own_concerns
        ]


@dataclass
class _ScriptedReviser:
    artifact_key: str
    name: str = "scripted"

    def revise(self, artifacts, concerns):  # type: ignore[no-untyped-def]
        # Mutate the doc each round so an accepter re-reviews (FR-012).
        body = artifacts.get(self.artifact_key, "") + "\nrevised"
        responses = [
            ConcernResponse(
                concern_id=c.id, response="addressed", what_changed="edit",
                artifacts_changed=[self.artifact_key],
            )
            for c in concerns
        ]
        return {self.artifact_key: body}, responses


def _build_spec(artifact_key: str, *, reviewers, reviser) -> ReviewSpec:
    # Stage "clarified" == the spec panel; its required extra inputs are
    # supplied below so run_engine_for_project's fail-loud check passes.
    return ReviewSpec(
        stage="clarified",
        artifacts=[artifact_key],
        reviewers=reviewers,
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


def _seed(tmp_path: Path) -> tuple[Path, Path, str]:
    repo = tmp_path / "repo"
    project_dir = repo / "projects" / "PROJ-902-x"
    feature = project_dir / "specs" / "001-x"
    feature.mkdir(parents=True)
    spec_md = feature / "spec.md"
    spec_md.write_text("# spec\n- **FR-001**: do X\n", encoding="utf-8")
    memory_dir = project_dir / ".specify" / "memory"
    return spec_md, memory_dir, str(spec_md.relative_to(repo))


def _extra_inputs() -> dict[str, str]:
    return {
        "__idea_md__": "idea body",
        "__comments_block__": "",
        "__spec_template__": "template",
    }


def _run(tmp_path: Path, *, reviewers, reviser):  # type: ignore[no-untyped-def]
    spec_md, memory_dir, key = _seed(tmp_path)
    repo = tmp_path / "repo"
    spec = _build_spec(key, reviewers=reviewers, reviser=reviser)
    run_stage_panel(
        stage_label="spec",
        spec=spec,
        artifact_paths={key: spec_md},
        extra_inputs=_extra_inputs(),
        repo_root=repo,
        memory_dir=memory_dir,
        producer=None,
    )
    return memory_dir, key


def test_nonconvergence_writes_convergence_kickback(tmp_path: Path) -> None:
    key = "projects/PROJ-902-x/specs/001-x/spec.md"
    concern = Concern(
        id="c1", reviewer="methodology", severity=Severity.SCIENCE,
        artifact=key, text="unsound method",
    )
    reviewer = _ScriptedReviewer("methodology", concern, accept_round=None)
    with pytest.raises(StagePanelKickback):
        memory_dir, _ = _run(
            tmp_path, reviewers=[reviewer], reviser=_ScriptedReviser(key),
        )
    memory_dir = tmp_path / "repo" / "projects" / "PROJ-902-x" / ".specify" / "memory"
    import yaml

    marker = memory_dir / "convergence_kickback.yaml"
    assert marker.exists()
    assert not (memory_dir / "human_input_needed.yaml").exists()
    payload = yaml.safe_load(marker.read_text())
    assert payload["to_stage"] == "flesh_out_in_progress"  # SCIENCE routing
    assert payload["stage"] == "spec"
    assert payload["unresolved_concerns"][0]["text"] == "unsound method"


def test_engine_exception_writes_human_input_needed(tmp_path: Path) -> None:
    key = "projects/PROJ-902-x/specs/001-x/spec.md"
    concern = Concern(
        id="c1", reviewer="methodology", severity=Severity.SCIENCE,
        artifact=key, text="x",
    )

    class _Boom(_ScriptedReviser):
        def revise(self, artifacts, concerns):  # type: ignore[no-untyped-def]
            raise RuntimeError("reviser exploded")

    reviewer = _ScriptedReviewer("methodology", concern, accept_round=None)
    with pytest.raises(StagePanelEscalation):
        _run(tmp_path, reviewers=[reviewer], reviser=_Boom(key))
    memory_dir = tmp_path / "repo" / "projects" / "PROJ-902-x" / ".specify" / "memory"
    # Genuine engine failure → human escalation, NOT the adaptive sentinel.
    assert (memory_dir / "human_input_needed.yaml").exists()
    assert not (memory_dir / "convergence_kickback.yaml").exists()


def test_transient_backend_error_does_not_escalate_to_human(tmp_path: Path) -> None:
    """A TRANSIENT backend failure (hung endpoint / 5xx, backend retries already
    exhausted) must NOT strand the project at human_input_needed — a human can't
    fix a degraded endpoint. It re-raises AS-IS (not StagePanelEscalation) so the
    run fails transiently and the project stays put to retry when the endpoint
    recovers. Regression for the PROJ-552 plan-panel false-escalation."""
    key = "projects/PROJ-902-x/specs/001-x/spec.md"
    concern = Concern(
        id="c1", reviewer="methodology", severity=Severity.SCIENCE,
        artifact=key, text="x",
    )

    class _Hung(_ScriptedReviser):
        def revise(self, artifacts, concerns):  # type: ignore[no-untyped-def]
            raise TransientBackendError(
                "Dartmouth model 'qwen.qwen3.5-122b' hung past 180s deadline"
            )

    reviewer = _ScriptedReviewer("methodology", concern, accept_round=None)
    # Re-raised as the raw transient — NOT wrapped in StagePanelEscalation.
    with pytest.raises(TransientBackendError):
        _run(tmp_path, reviewers=[reviewer], reviser=_Hung(key))
    memory_dir = tmp_path / "repo" / "projects" / "PROJ-902-x" / ".specify" / "memory"
    # Crucially: NO human-escalation marker and NO kickback sentinel were written.
    assert not (memory_dir / "human_input_needed.yaml").exists()
    assert not (memory_dir / "convergence_kickback.yaml").exists()


def test_on_round_trail_persisted(tmp_path: Path) -> None:
    key = "projects/PROJ-902-x/specs/001-x/spec.md"
    concern = Concern(
        id="c1", reviewer="methodology", severity=Severity.WRITING,
        artifact=key, text="nit",
    )
    # Accept on round 2 → multiple rounds run → a multi-line trail.
    reviewer = _ScriptedReviewer("methodology", concern, accept_round=2)
    memory_dir, _ = _run(
        tmp_path, reviewers=[reviewer], reviser=_ScriptedReviser(key),
    )
    trail_dir = memory_dir / "convergence_trail"
    files = list(trail_dir.glob("spec-*.jsonl"))
    assert len(files) == 1
    lines = [
        json.loads(line)
        for line in files[0].read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) >= 2  # R1 + at least one revise/re-review round
    assert lines[0]["round"] == 1
    assert lines[0]["concerns"]  # R1 raised the concern


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
