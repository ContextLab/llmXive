"""T024: speckit_prune unit tests with transitive deletion + recursive rollback."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import yaml

from llmxive.audit.speckit_prune import (
    audit_artifacts,
    prune_templates,
    _walk_back_to_real_stage,
)


_FIXTURES_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "audit"

REAL_SPEC = (_FIXTURES_ROOT / "speckit_real" / "spec.md").read_text()
TEMPLATE_SPEC = (_FIXTURES_ROOT / "speckit_template" / "spec.md").read_text()


def _seed_templates_dir(repo_root: Path) -> None:
    """Copy the real spec templates into the fixture repo so _real_only_guard
    can compare candidate artifacts against them (the auditor's similarity check
    uses these as the reference template set)."""
    src = Path(__file__).resolve().parents[2] / ".specify" / "templates"
    dst = repo_root / ".specify" / "templates"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        import shutil
        shutil.copytree(src, dst, dirs_exist_ok=True)


def _make_project(repo_root: Path, proj_id: str, *, spec_text: str, plan_text: str, tasks_text: str | None = None) -> None:
    """Create a fixture project with the given artifact contents."""
    _seed_templates_dir(repo_root)
    spec_dir = repo_root / "projects" / proj_id / "specs" / "001-foo"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "spec.md").write_text(spec_text)
    (spec_dir / "plan.md").write_text(plan_text)
    if tasks_text is not None:
        (spec_dir / "tasks.md").write_text(tasks_text)

    state_dir = repo_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = state_dir / f"{proj_id}.yaml"
    yaml_path.write_text(yaml.safe_dump({"id": proj_id, "current_stage": "tasked"}))
    history_path = state_dir / f"{proj_id}.history.jsonl"
    history_path.write_text(
        "\n".join(
            json.dumps(e)
            for e in [
                {"event": "advance", "to_stage": "specified", "ts": "2026-05-14T00:00:00Z"},
                {"event": "advance", "to_stage": "planned", "ts": "2026-05-14T01:00:00Z"},
                {"event": "advance", "to_stage": "tasked", "ts": "2026-05-14T02:00:00Z"},
            ]
        ) + "\n"
    )


class TestAuditArtifacts(unittest.TestCase):
    def test_audit_classifies_real_vs_template(self) -> None:
        with TemporaryDirectory() as d:
            repo = Path(d)
            _make_project(
                repo,
                "PROJ-001-foo",
                spec_text=REAL_SPEC,
                plan_text=REAL_SPEC,  # Use real content for plan too
            )
            _make_project(
                repo,
                "PROJ-002-bar",
                spec_text=TEMPLATE_SPEC,
                plan_text=REAL_SPEC,
            )
            report = audit_artifacts(repo)
        self.assertGreaterEqual(report["total_artifacts"], 2)
        templates = [a for a in report["artifacts"] if a["classification"] == "TEMPLATE"]
        self.assertGreaterEqual(len(templates), 1)
        # PROJ-002-bar's spec should be the template
        template_paths = [a["path"] for a in templates]
        self.assertTrue(
            any("PROJ-002-bar" in p and "spec.md" in p for p in template_paths),
            f"expected PROJ-002-bar/spec.md in templates: {template_paths}",
        )


class TestPruneTransitiveDeletion(unittest.TestCase):
    def test_template_spec_with_downstream_artifacts_deleted_transitively(self) -> None:
        """Per FR-008 + C9: TEMPLATE spec.md → also delete downstream tasks.md."""
        with TemporaryDirectory() as d:
            repo = Path(d)
            _make_project(
                repo,
                "PROJ-100-foo",
                spec_text=TEMPLATE_SPEC,
                plan_text=REAL_SPEC,  # real
                tasks_text=TEMPLATE_SPEC,  # also template (downstream of spec)
            )
            spec_dir = repo / "projects" / "PROJ-100-foo" / "specs" / "001-foo"
            # Sanity: all three files exist initially
            self.assertTrue((spec_dir / "spec.md").exists())
            self.assertTrue((spec_dir / "plan.md").exists())
            self.assertTrue((spec_dir / "tasks.md").exists())

            report = prune_templates(repo, apply=True)

            # spec.md and tasks.md (template) gone; plan.md (real) survives.
            self.assertFalse((spec_dir / "spec.md").exists(), "spec.md should be deleted")
            self.assertFalse(
                (spec_dir / "tasks.md").exists(),
                "tasks.md should be deleted transitively",
            )
            self.assertTrue((spec_dir / "plan.md").exists(), "real plan.md preserved")

            # State rolled back to a pre-tasked stage; history event recorded.
            yaml_doc = yaml.safe_load(
                (repo / "state" / "projects" / "PROJ-100-foo.yaml").read_text()
            )
            self.assertNotEqual(yaml_doc["current_stage"], "tasked")
            history = (
                repo / "state" / "projects" / "PROJ-100-foo.history.jsonl"
            ).read_text()
            self.assertIn("template_artifact_purge", history)


class TestWalkBackToRealStage(unittest.TestCase):
    def test_walks_back_until_real(self) -> None:
        with TemporaryDirectory() as d:
            repo = Path(d)
            _make_project(
                repo,
                "PROJ-200-baz",
                spec_text=TEMPLATE_SPEC,   # templated → skip
                plan_text=REAL_SPEC,        # real → stage 'planned' wins
                tasks_text=TEMPLATE_SPEC,   # templated → skip
            )
            history = repo / "state" / "projects" / "PROJ-200-baz.history.jsonl"
            stage = _walk_back_to_real_stage(history, repo)
            # 'planned' is the latest stage whose expected artifact (plan.md) is real
            self.assertEqual(stage, "planned")

    def test_no_history_returns_flesh_out_complete(self) -> None:
        with TemporaryDirectory() as d:
            history = Path(d) / "nonexistent.history.jsonl"
            self.assertEqual(
                _walk_back_to_real_stage(history, Path(d)),
                "flesh_out_complete",
            )


class TestDryRun(unittest.TestCase):
    def test_dry_run_makes_no_filesystem_changes(self) -> None:
        with TemporaryDirectory() as d:
            repo = Path(d)
            _make_project(
                repo,
                "PROJ-300-q",
                spec_text=TEMPLATE_SPEC,
                plan_text=REAL_SPEC,
            )
            spec_dir = repo / "projects" / "PROJ-300-q" / "specs" / "001-foo"
            before = sorted(p.name for p in spec_dir.glob("*.md"))
            report = prune_templates(repo, apply=False)
            after = sorted(p.name for p in spec_dir.glob("*.md"))
            self.assertEqual(before, after)
            self.assertFalse(report.get("deleted_paths"))


if __name__ == "__main__":
    unittest.main()
