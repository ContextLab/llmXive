"""T012: real-filesystem tests for src/llmxive/feed/store.py

Constitution III: real filesystem, no mocks. Each test creates a temp dir,
exercises FeedStore against it, and verifies actual file contents.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from llmxive.feed import FeedStore
from llmxive.feed.store import utcnow_iso


def _make_repo(project_id: str = "PROJ-TEST-001") -> tuple[Path, str]:
    root = Path(tempfile.mkdtemp(prefix="feed_test_"))
    (root / "projects" / project_id).mkdir(parents=True)
    return root, project_id


def _author(name: str = "test-agent") -> dict:
    return {"type": "agent", "name": name}


class TestFeedStoreAppend(unittest.TestCase):
    def setUp(self):
        self.root, self.pid = _make_repo()
        self.store = FeedStore(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_append_writes_jsonl(self):
        item = {
            "kind": "human_comment",
            "author": _author("alice"),
            "summary": "first comment",
            "body": "this is the first comment",
        }
        written = self.store.append(self.pid, item)
        self.assertIn("id", written)
        self.assertEqual(written["kind"], "human_comment")
        self.assertEqual(written["audit_status"], "live")

        path = self.root / "projects" / self.pid / "activity.jsonl"
        self.assertTrue(path.exists())
        line = path.read_text().splitlines()[0]
        parsed = json.loads(line)
        self.assertEqual(parsed["id"], written["id"])

    def test_append_rejects_missing_required(self):
        # No 'kind' field — must fail-fast
        with self.assertRaises(ValueError) as cm:
            self.store.append(self.pid, {"author": _author(), "summary": "x"})
        self.assertIn("kind", str(cm.exception))

    def test_read_returns_live_only_by_default(self):
        self.store.append(self.pid, {
            "kind": "human_comment", "author": _author(), "summary": "live one"
        })
        # Manually inject a rejected item
        path = self.root / "projects" / self.pid / "activity.jsonl"
        with open(path, "a") as f:
            f.write(json.dumps({
                "id": "01ARZ3NDEKTSV4RRFFQ69G5FAA",
                "kind": "personality_tick",
                "author": _author("aristotle"),
                "summary": "rejected",
                "created_at": utcnow_iso(),
                "audit_status": "rejected",
            }) + "\n")
        live = self.store.read(self.pid)
        self.assertEqual(len(live), 1)
        self.assertEqual(live[0]["summary"], "live one")
        all_ = self.store.read(self.pid, include_audit_statuses={"live", "rejected"})
        self.assertEqual(len(all_), 2)


class TestFeedStoreEditAndRetract(unittest.TestCase):
    def setUp(self):
        self.root, self.pid = _make_repo()
        self.store = FeedStore(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_edit_appends_edit_item_and_preserves_original(self):
        item = self.store.append(self.pid, {
            "kind": "human_comment", "author": _author("alice"),
            "summary": "v1", "body": "original body",
        })
        editor = _author("alice")
        self.store.edit(self.pid, item["id"], "edited body", editor)

        # Read returns current text (edited) and edited_at marker
        live = self.store.read(self.pid)
        self.assertEqual(len(live), 1)
        self.assertEqual(live[0]["body"], "edited body")
        self.assertIsNotNone(live[0].get("edited_at"))

        # Original lives in audit log
        history = self.root / "projects" / self.pid / ".audit" / "edit-history.jsonl"
        self.assertTrue(history.exists())
        record = json.loads(history.read_text().splitlines()[0])
        self.assertEqual(record["original_body"], "original body")

    def test_retract_flips_status_to_superseded(self):
        item = self.store.append(self.pid, {
            "kind": "human_comment", "author": _author(), "summary": "x", "body": "y"
        })
        self.store.retract(self.pid, item["id"], "wrong claim", _author())
        live = self.store.read(self.pid)
        self.assertEqual(len(live), 0, "retracted item should not appear in live feed")
        all_ = self.store.read(self.pid, include_audit_statuses={"live", "superseded"})
        self.assertEqual(len(all_), 1)
        self.assertEqual(all_[0]["audit_status"], "superseded")


class TestFeedStorePack(unittest.TestCase):
    def setUp(self):
        self.root, self.pid = _make_repo()
        self.store = FeedStore(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_pack_no_truncation_under_budget(self):
        for i in range(3):
            self.store.append(self.pid, {
                "kind": "human_comment", "author": _author(),
                "summary": f"s{i}", "body": f"b{i}",
            })
        packed = self.store.pack_for_dispatch(self.pid, budget_chars=10000)
        self.assertEqual(len(packed.items), 3)
        self.assertEqual(packed.truncated, 0)
        self.assertIsNone(packed.truncation_marker)

    def test_pack_truncates_from_oldest(self):
        # Make 30 items with sizable bodies; budget is very small
        for i in range(30):
            self.store.append(self.pid, {
                "kind": "human_comment", "author": _author(),
                "summary": f"item-{i}", "body": "x" * 500,
            })
        packed = self.store.pack_for_dispatch(self.pid, budget_chars=2000)
        # Newest items retained, oldest truncated
        self.assertGreater(packed.truncated, 0)
        self.assertIsNotNone(packed.truncation_marker)
        self.assertIn("truncated", packed.truncation_marker)
        # The retained items should be the newest ones
        if packed.items:
            self.assertIn("item-2", packed.items[-1]["summary"])

    def test_pack_includes_truncation_marker_in_block(self):
        for i in range(10):
            self.store.append(self.pid, {
                "kind": "human_comment", "author": _author(),
                "summary": f"item-{i}", "body": "y" * 1000,
            })
        packed = self.store.pack_for_dispatch(self.pid, budget_chars=1500)
        block = packed.to_context_block()
        self.assertIn("truncated", block.lower())


class TestFeedStoreDispatchLedger(unittest.TestCase):
    def setUp(self):
        self.root, self.pid = _make_repo()
        self.store = FeedStore(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_record_dispatch_appends_to_jsonl(self):
        self.store.record_dispatch(self.pid, {
            "dispatch_id": "01ARZ3NDEKTSV4RRFFQ69G5FAA",
            "agent": "test-agent",
            "feed_delivered": True,
        })
        # Check the file exists under .audit/dispatches/
        ddir = self.root / "projects" / self.pid / ".audit" / "dispatches"
        self.assertTrue(ddir.exists())
        files = list(ddir.glob("*.jsonl"))
        self.assertEqual(len(files), 1)
        record = json.loads(files[0].read_text().splitlines()[0])
        self.assertEqual(record["agent"], "test-agent")
        self.assertIn("dispatched_at", record)

    def test_record_rejected_appends_to_audit(self):
        self.store.record_rejected(self.pid, {
            "id": "X", "kind": "personality_tick", "reason": "rubric_failure_after_retry"
        })
        path = self.root / "projects" / self.pid / ".audit" / "rejected-contributions.jsonl"
        self.assertTrue(path.exists())
        self.assertEqual(len(path.read_text().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
