"""T063: feedback-loop auditor unit tests (FR-034).

Seeds a project with an activity feed + a dispatch record, runs the
auditor, asserts pass/fail classifications matching the spec.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from llmxive.audit.feedback_loop import audit


def _setup_project(root: Path, pid: str = "PROJ-TEST-FL-001") -> Path:
    pdir = root / "projects" / pid
    pdir.mkdir(parents=True)
    (pdir / ".audit" / "dispatches").mkdir(parents=True)
    return pdir


def _write_feed(pdir: Path, items: list[dict]):
    fp = pdir / "activity.jsonl"
    fp.write_text("\n".join(json.dumps(i) for i in items) + "\n")


def _write_dispatches(pdir: Path, records: list[dict]):
    fp = pdir / ".audit" / "dispatches" / "2026-05-14.jsonl"
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text("\n".join(json.dumps(r) for r in records) + "\n")


class TestFeedbackLoopAudit(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="audit_fl_"))
        self.pdir = _setup_project(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_valid_dispatch_classifies_passes(self):
        # Feed has one item; dispatch references it via a valid manifest
        feed_id = "01ARZ3NDEKTSV4RRFFQ69G5FAA"
        _write_feed(self.pdir, [{
            "id": feed_id, "kind": "personality_tick",
            "author": {"type": "agent", "name": "ada"},
            "summary": "x", "audit_status": "live",
        }])
        _write_dispatches(self.pdir, [{
            "dispatch_id": "01ARZ3NDEKTSV4RRFFQ69G5FBB",
            "agent": "personality:aristotle",
            "feed_delivered": True,
            "manifest": {
                "items": [{"feed_item_id": feed_id, "response": "addressed"}],
            },
        }])
        manifest = audit(projects_dir=self.root / "projects", repo_root=self.root)
        by_cls = manifest["summary"]["by_classification"]
        self.assertEqual(by_cls.get("passes", 0), 1)
        self.assertEqual(by_cls.get("fails", 0), 0)

    def test_missing_manifest_classifies_fails(self):
        _write_feed(self.pdir, [{
            "id": "01ARZ3NDEKTSV4RRFFQ69G5FAA",
            "kind": "personality_tick",
            "author": {"type": "agent", "name": "ada"},
            "summary": "x", "audit_status": "live",
        }])
        _write_dispatches(self.pdir, [{
            "dispatch_id": "01ARZ3NDEKTSV4RRFFQ69G5FBB",
            "agent": "personality:aristotle",
            "feed_delivered": True,
            # No manifest field
        }])
        manifest = audit(projects_dir=self.root / "projects", repo_root=self.root)
        self.assertEqual(manifest["summary"]["by_classification"].get("fails", 0), 1)

    def test_bogus_feed_id_classifies_fails(self):
        _write_feed(self.pdir, [{
            "id": "01ARZ3NDEKTSV4RRFFQ69G5FAA",
            "kind": "personality_tick",
            "author": {"type": "agent", "name": "ada"},
            "summary": "x", "audit_status": "live",
        }])
        _write_dispatches(self.pdir, [{
            "dispatch_id": "01ARZ3NDEKTSV4RRFFQ69G5FBB",
            "agent": "x",
            "feed_delivered": True,
            "manifest": {
                "items": [{"feed_item_id": "01XXXXXXXXXXXXXXXXXXXXXXXX",
                           "response": "addressed"}],
            },
        }])
        manifest = audit(projects_dir=self.root / "projects", repo_root=self.root)
        self.assertEqual(manifest["summary"]["by_classification"].get("fails", 0), 1)
        rule_ids = []
        for it in manifest["items"]:
            rule_ids.extend(r["rule_id"] for r in it["rules_fired"])
        self.assertIn("manifest_references_bogus_feed_ids", rule_ids)

    def test_feed_not_delivered_classifies_fails(self):
        _write_feed(self.pdir, [])
        _write_dispatches(self.pdir, [{
            "dispatch_id": "X", "agent": "x",
            "feed_delivered": False,
        }])
        manifest = audit(projects_dir=self.root / "projects", repo_root=self.root)
        self.assertEqual(manifest["summary"]["by_classification"].get("fails", 0), 1)

    def test_since_filter_excludes_older(self):
        _write_feed(self.pdir, [])
        _write_dispatches(self.pdir, [
            {"dispatch_id": "old", "agent": "x", "feed_delivered": True,
             "manifest": {"items": []}, "dispatched_at": "2020-01-01T00:00:00.000000Z"},
            {"dispatch_id": "new", "agent": "x", "feed_delivered": True,
             "manifest": {"items": []}, "dispatched_at": "2030-01-01T00:00:00.000000Z"},
        ])
        manifest = audit(
            projects_dir=self.root / "projects",
            repo_root=self.root,
            since="2025-01-01T00:00:00.000000Z",
        )
        # Only the "new" record is in-window
        self.assertEqual(manifest["summary"]["total"], 1)


if __name__ == "__main__":
    unittest.main()
