"""Unit tests for the engine ↔ auto-revisions directory adapter
(spec 015 T042 / FR-034).

The adapter is the SOLE bridge from the convergence engine's
``KickbackRecord`` to the implementer's on-disk read contract under
``specs/auto-revisions/<PROJ-ID>/round-<N>/``. These tests verify the
directory contract end-to-end on real filesystem fixtures (no Mocks).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from llmxive.convergence.revision_adapter import (
    _legacy_severity,
    _render_plan,
    _render_spec,
    _render_tasks,
    kickback_to_revision_spec,
    next_round_number,
)
from llmxive.convergence.types import (
    Concern,
    KickbackRecord,
    Severity,
)


def _make_concern(
    *, id_: str = "abc123def456", severity: Severity = Severity.WRITING,
    text: str = "Fix typo in abstract.",
    reviewer: str = "paper_reviewer",
    artifact: str = "projects/PROJ-100-test/paper/source/main.tex",
) -> Concern:
    return Concern(
        id=id_,
        reviewer=reviewer,
        severity=severity,
        artifact=artifact,
        location="",
        text=text,
        round=1,
    )


def _make_kickback(concerns: list[Concern], *, worst: Severity = Severity.WRITING) -> KickbackRecord:
    return KickbackRecord(
        from_stage="paper_review",
        to_stage="paper_tasked",
        worst_severity=worst,
        unresolved_concerns=concerns,
        artifact_links=["projects/PROJ-100-test/paper/source/"],
        reason="test kickback",
    )


class TestRevisionAdapterDirectoryContract:
    """The directory written must contain spec.md, plan.md, tasks.md,
    analyze-report.md, result.yaml AND state/revisions/index.yaml
    must be updated with a `ready` entry."""

    def test_emits_all_five_artifacts(self, tmp_path: Path) -> None:
        kb = _make_kickback([_make_concern()])
        spec_dir = kickback_to_revision_spec(
            kb, project_id="PROJ-100-test", repo_root=tmp_path,
        )
        assert spec_dir.is_dir()
        assert (spec_dir / "spec.md").is_file()
        assert (spec_dir / "plan.md").is_file()
        assert (spec_dir / "tasks.md").is_file()
        assert (spec_dir / "analyze-report.md").is_file()
        assert (spec_dir / "result.yaml").is_file()

    def test_round_directory_pattern(self, tmp_path: Path) -> None:
        kb = _make_kickback([_make_concern()])
        spec_dir = kickback_to_revision_spec(
            kb, project_id="PROJ-100-test", repo_root=tmp_path,
        )
        # First round numbered 1.
        assert spec_dir.name == "round-1"
        # Located at specs/auto-revisions/<PROJ-ID>/
        parent = spec_dir.parent
        assert parent.name == "PROJ-100-test"
        assert parent.parent.name == "auto-revisions"
        assert parent.parent.parent.name == "specs"

    def test_index_yaml_updated_with_ready_entry(self, tmp_path: Path) -> None:
        kb = _make_kickback([_make_concern()])
        kickback_to_revision_spec(kb, project_id="PROJ-100-test", repo_root=tmp_path)
        idx_path = tmp_path / "state" / "revisions" / "index.yaml"
        assert idx_path.is_file()
        idx = yaml.safe_load(idx_path.read_text(encoding="utf-8"))
        assert "ready" in idx
        assert len(idx["ready"]) == 1
        assert idx["ready"][0]["project_id"] == "PROJ-100-test"
        assert "round-1" in idx["ready"][0]["revision_spec_path"]

    def test_tasks_md_contains_one_task_per_concern(self, tmp_path: Path) -> None:
        concerns = [
            _make_concern(id_="aaaaaaaaaaaa", text="Concern A", severity=Severity.WRITING),
            _make_concern(id_="bbbbbbbbbbbb", text="Concern B", severity=Severity.SCIENCE),
            _make_concern(id_="cccccccccccc", text="Concern C", severity=Severity.METHODOLOGY),
        ]
        kb = _make_kickback(concerns, worst=Severity.SCIENCE)
        spec_dir = kickback_to_revision_spec(
            kb, project_id="PROJ-100-test", repo_root=tmp_path,
        )
        tasks = (spec_dir / "tasks.md").read_text()
        assert tasks.count("- [ ] T") == 3
        # All concern ids surface in tasks.md.
        assert "[aaaaaaaaaaaa]" in tasks
        assert "[bbbbbbbbbbbb]" in tasks
        assert "[cccccccccccc]" in tasks

    def test_result_yaml_contains_engine_severity(self, tmp_path: Path) -> None:
        kb = _make_kickback([_make_concern(severity=Severity.METHODOLOGY)],
                            worst=Severity.METHODOLOGY)
        spec_dir = kickback_to_revision_spec(
            kb, project_id="PROJ-100-test", repo_root=tmp_path,
        )
        result = yaml.safe_load((spec_dir / "result.yaml").read_text())
        assert result["worst_severity"] == "methodology"
        assert result["from_stage"] == "paper_review"
        assert result["final_outcome"] == "ready_for_implementation"
        assert len(result["seed_action_items"]) == 1
        assert result["seed_action_items"][0]["engine_severity"] == "methodology"
        # Legacy severity is "science" for METHODOLOGY (the legacy
        # taxonomy collapses methodology+science).
        assert result["seed_action_items"][0]["severity"] == "science"


class TestRevisionAdapterRoundNumbering:
    def test_next_round_is_one_for_fresh_project(self, tmp_path: Path) -> None:
        assert next_round_number(tmp_path, "PROJ-100-test") == 1

    def test_next_round_increments_with_existing_rounds(self, tmp_path: Path) -> None:
        base = tmp_path / "specs" / "auto-revisions" / "PROJ-100-test"
        (base / "round-1").mkdir(parents=True)
        (base / "round-2").mkdir()
        (base / "round-5").mkdir()  # gap is OK
        assert next_round_number(tmp_path, "PROJ-100-test") == 6

    def test_consecutive_adapter_calls_increment_round(self, tmp_path: Path) -> None:
        kb = _make_kickback([_make_concern()])
        d1 = kickback_to_revision_spec(kb, project_id="PROJ-100-test", repo_root=tmp_path)
        d2 = kickback_to_revision_spec(kb, project_id="PROJ-100-test", repo_root=tmp_path)
        assert d1.name == "round-1"
        assert d2.name == "round-2"


class TestRevisionAdapterTaskOrdering:
    """The legacy revision_planner sorted tasks by severity:
    writing(0) < science(1) < fatal(2). The adapter must preserve that
    order so the implementer's per-task processing matches the legacy
    behaviour (writing first, science second, fatal last)."""

    def test_writing_concerns_listed_first(self, tmp_path: Path) -> None:
        concerns = [
            _make_concern(id_="111111111111", severity=Severity.SCIENCE, text="Sci"),
            _make_concern(id_="222222222222", severity=Severity.WRITING, text="Wri"),
            _make_concern(id_="333333333333", severity=Severity.FATAL, text="Fat"),
        ]
        spec_dir = kickback_to_revision_spec(
            _make_kickback(concerns, worst=Severity.FATAL),
            project_id="PROJ-100-test", repo_root=tmp_path,
        )
        tasks = (spec_dir / "tasks.md").read_text()
        pos_w = tasks.index("[222222222222]")
        pos_s = tasks.index("[111111111111]")
        pos_f = tasks.index("[333333333333]")
        assert pos_w < pos_s < pos_f


class TestLegacySeverityMap:
    def test_writing_methodology_science_fatal(self) -> None:
        assert _legacy_severity(Severity.WRITING) == "writing"
        assert _legacy_severity(Severity.METHODOLOGY) == "science"
        assert _legacy_severity(Severity.SCIENCE) == "science"
        assert _legacy_severity(Severity.FATAL) == "fatal"
        assert _legacy_severity(Severity.CODE) == "writing"
        assert _legacy_severity(Severity.REQUIREMENT) == "writing"
        assert _legacy_severity(Severity.TRIVIAL) == "writing"


class TestEmptyConcernsDefensive:
    """An empty seed shouldn't crash — the adapter writes a defensive
    "no action items" task placeholder (preserves the legacy contract)."""

    def test_zero_concerns_writes_placeholder_task(self, tmp_path: Path) -> None:
        kb = KickbackRecord(
            from_stage="paper_review",
            to_stage="paper_tasked",
            worst_severity=Severity.WRITING,
            unresolved_concerns=[],  # defensive — engine shouldn't emit this normally
            artifact_links=[],
            reason="defensive empty seed test",
        )
        spec_dir = kickback_to_revision_spec(
            kb, project_id="PROJ-100-test", repo_root=tmp_path,
        )
        tasks = (spec_dir / "tasks.md").read_text()
        assert "T001" in tasks
        assert "empty seed" in tasks


class TestRenderHelpersByteCompatibility:
    """Render helpers must remain stable so the implementer's parsers
    keep working unchanged."""

    def test_spec_contains_input_section(self) -> None:
        c = _make_concern(text="Add citation.")
        spec_text = _render_spec([c], "paper_writing", "PROJ-100-test", 1)
        assert "## Input" in spec_text
        assert "Add citation" in spec_text
        assert "abc123def456" in spec_text  # concern id
        assert "## Success Criterion" in spec_text

    def test_plan_severity_counts(self) -> None:
        concerns = [
            _make_concern(id_="aaaaaaaaaaaa", severity=Severity.WRITING),
            _make_concern(id_="bbbbbbbbbbbb", severity=Severity.WRITING),
            _make_concern(id_="cccccccccccc", severity=Severity.SCIENCE),
        ]
        plan_text = _render_plan(concerns, "paper_writing")
        assert "writing=2" in plan_text
        assert "science=1" in plan_text

    def test_tasks_md_format_matches_legacy(self) -> None:
        c = _make_concern(id_="deadbeefcafe", text="Fix it", severity=Severity.WRITING)
        tasks_text = _render_tasks([c])
        # Legacy format pattern: "- [ ] T001 [REV] Address action item **[<id>]** (severity: <sev>): <text>"
        assert "- [ ] T001 [REV] Address action item **[deadbeefcafe]**" in tasks_text
        assert "(severity: writing)" in tasks_text
        assert "Fix it" in tasks_text
