"""Empty ticks skip setup without suppressing legacy or uncertain work."""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/ci/reprocess_queue.py"
spec = importlib.util.spec_from_file_location("reprocess_queue", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


@pytest.mark.parametrize("stage", ["paper_ingested", "paper_review"])
def test_pending_or_legacy_migration_runs_without_paper_metadata(tmp_path, stage):
    # No paper directory/classification is available in the sparse checkout.
    (tmp_path / "external.yaml").write_text(f"current_stage: {stage}\n")
    assert probe.needs_drain(tmp_path)[0]


def test_authored_review_is_conservatively_left_to_real_migrator(tmp_path):
    (tmp_path / "authored.yaml").write_text(
        "current_stage: paper_review\nspeckit_research_dir: projects/authored/.specify\n"
    )
    assert probe.needs_drain(tmp_path)[0]


def test_empty_queue_emits_false_and_retains_read_only_state(tmp_path):
    for stage in ["in_progress", "planned", "reviewed_preprint"]:
        (tmp_path / f"{stage}.yaml").write_text(f"current_stage: {stage}\n")
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--state-dir", str(tmp_path)],
        capture_output=True, text=True, check=True,
    )
    assert result.stdout == "needed=false\n"
    assert "3 project records" in result.stderr
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}


@pytest.mark.parametrize("body", ["[", "null", "[]", "id: project", "current_stage: null",
                                     "current_stage: ''", "current_stage: [paper_review]",
                                     "current_stage: future_unknown_stage"])
def test_uncertain_yaml_cannot_hide_work(tmp_path, body):
    (tmp_path / "project.yaml").write_text(body)
    assert probe.needs_drain(tmp_path)[0]


def test_missing_stage_vocabulary_runs_normal_checks(tmp_path, monkeypatch):
    (tmp_path / "project.yaml").write_text("current_stage: planned\n")
    monkeypatch.setattr(probe, "SCHEMA", tmp_path / "absent-schema.yaml")
    assert probe.needs_drain(tmp_path)[0]


def test_missing_empty_and_unreadable_state_run_normal_checks(tmp_path):
    assert probe.needs_drain(tmp_path / "missing")[0]
    assert probe.needs_drain(tmp_path)[0]
    (tmp_path / "project.yaml").write_bytes(b"\xff")
    assert probe.needs_drain(tmp_path)[0]


def test_workflow_preserves_manual_failure_and_snapshot_routes():
    workflow = yaml.safe_load((ROOT / ".github/workflows/reprocess.yml").read_text())
    queue = workflow["jobs"]["queue"]
    drain = workflow["jobs"]["drain"]
    condition = drain["if"]
    assert "!cancelled()" in condition
    assert "github.event_name == 'workflow_dispatch'" in condition
    assert "needs.queue.result != 'success'" in condition
    assert "needs.queue.outputs.needed != 'false'" in condition
    assert queue["outputs"]["commit"] == "${{ steps.checkout.outputs.commit }}"
    assert drain["steps"][0]["with"]["ref"] == "${{ needs.queue.outputs.commit || 'main' }}"
    commands = "\n".join(s.get("run", "") for s in drain["steps"])
    for required in ["install-texlive.sh", "poppler-utils", "llmxive preflight",
                     "migrate_unprocessed_external_papers", "--stage paper_ingested", "commit-and-push.sh"]:
        assert required in commands
