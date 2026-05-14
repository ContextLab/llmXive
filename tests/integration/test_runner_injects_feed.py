"""T064-T069: runner integration tests for FR-026, FR-028, FR-030, FR-031, FR-033.

Exercises the SINGLE integration point (src/llmxive/agents/runner.py) using
a stub agent. Real filesystem + real FeedStore (no mocks of the feed); we
only stub the Agent's `run()` to avoid LLM invocation.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from llmxive.agents.base import Agent, AgentContext
from llmxive.agents.runner import run_agent
from llmxive.feed import FeedStore


class StubAgent:
    """Minimal duck-typed Agent that records the ctx it was invoked with.

    Does NOT subclass Agent (which has abstract methods + Pydantic-validated
    return values) — runner.run_agent only needs `.name` and `.run(ctx)`.
    """

    def __init__(self, name: str = "stub"):
        self.name = name
        self.last_ctx: AgentContext | None = None

    def run(self, ctx: AgentContext):
        self.last_ctx = ctx
        return None  # runner doesn't introspect this in our test paths


def _seed_project(root: Path, pid: str = "PROJ-001-test-f", items: list[dict] | None = None) -> Path:
    pdir = root / "projects" / pid
    pdir.mkdir(parents=True)
    store = FeedStore(root)
    for item in (items or []):
        store.append(pid, item)
    return pdir


def _ctx(pid: str) -> AgentContext:
    return AgentContext(
        project_id=pid, run_id="run-x", task_id="task-x",
        inputs=[],
    )


class TestRunnerInjectsFeed(unittest.TestCase):
    """T064: runner injects feed into agent context."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="runner_inject_"))
        self.pid = "PROJ-001-test-f"
        _seed_project(self.root, self.pid, items=[
            {"kind": "human_comment", "author": {"type": "human", "name": "alice"},
             "summary": "first", "body": "first comment"},
            {"kind": "human_comment", "author": {"type": "human", "name": "bob"},
             "summary": "second", "body": "second comment"},
        ])

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_agent_sees_feed_in_ctx(self):
        agent = StubAgent()
        run_agent(agent, _ctx(self.pid), repo_root=self.root)
        self.assertIsNotNone(agent.last_ctx)
        self.assertTrue(agent.last_ctx.feed_context)
        self.assertIn("first comment", agent.last_ctx.feed_context)
        self.assertIn("second comment", agent.last_ctx.feed_context)
        self.assertTrue(agent.last_ctx.dispatch_id)
        self.assertTrue(agent.last_ctx.feed_snapshot_at)

    def test_dispatch_recorded_to_ledger(self):
        agent = StubAgent()
        run_agent(agent, _ctx(self.pid), repo_root=self.root)
        ddir = self.root / "projects" / self.pid / ".audit" / "dispatches"
        self.assertTrue(ddir.exists())
        files = list(ddir.glob("*.jsonl"))
        self.assertEqual(len(files), 1)
        record = json.loads(files[0].read_text().splitlines()[0])
        self.assertEqual(record["agent"], "stub")
        self.assertTrue(record["feed_delivered"])
        self.assertTrue(record["dispatch_id"])

    def test_inject_feed_disabled_skips_injection(self):
        agent = StubAgent()
        run_agent(agent, _ctx(self.pid), repo_root=self.root, inject_feed=False)
        self.assertEqual(agent.last_ctx.feed_context, "")
        # Dispatch ledger also not written when inject_feed=False
        ddir = self.root / "projects" / self.pid / ".audit" / "dispatches"
        self.assertFalse(ddir.exists())


class TestRunnerFiltersRejectedContributions(unittest.TestCase):
    """T066 (FR-030): rejected/superseded items must NOT reach agent context."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="runner_filter_"))
        self.pid = "PROJ-002-test-fr"
        _seed_project(self.root, self.pid)
        store = FeedStore(self.root)
        # One live, one rejected
        live = store.append(self.pid, {
            "kind": "human_comment", "author": {"type": "human", "name": "alice"},
            "summary": "LIVE_ITEM", "body": "live body",
        })
        # Append a rejected item directly to the JSONL (bypassing the
        # default audit_status=live coercion)
        path = self.root / "projects" / self.pid / "activity.jsonl"
        with open(path, "a") as f:
            f.write(json.dumps({
                "id": "01XREJREJREJREJREJREJREJ00",
                "kind": "personality_tick",
                "author": {"type": "agent", "name": "fake"},
                "summary": "REJECTED_ITEM",
                "body": "REJECTED_BODY_SHOULD_NEVER_APPEAR",
                "created_at": "2026-05-14T09:00:00.000000Z",
                "audit_status": "rejected",
            }) + "\n")
        self.live_id = live["id"]

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_rejected_item_absent_from_feed_context(self):
        agent = StubAgent()
        run_agent(agent, _ctx(self.pid), repo_root=self.root)
        self.assertIn("LIVE_ITEM", agent.last_ctx.feed_context)
        self.assertNotIn("REJECTED_ITEM", agent.last_ctx.feed_context)
        self.assertNotIn("REJECTED_BODY_SHOULD_NEVER_APPEAR", agent.last_ctx.feed_context)


class TestRunnerTruncatesFromOldest(unittest.TestCase):
    """T067 (FR-031): runner truncates from oldest with a visible marker."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="runner_trunc_"))
        self.pid = "PROJ-003-test-tr"
        # Each item has a fat summary so even summary-only packing overruns budget
        big_summary = "summary-" + "x" * 250
        items = [
            {"kind": "human_comment", "author": {"type": "human", "name": "a"},
             "summary": big_summary + f"-{i}", "body": "y" * 500}
            for i in range(60)
        ]
        _seed_project(self.root, self.pid, items=items)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_truncation_marker_visible(self):
        agent = StubAgent()
        # Tiny budget forces truncation
        from llmxive.agents import runner as runner_module
        original = runner_module.DEFAULT_FEED_BUDGET
        runner_module.DEFAULT_FEED_BUDGET = 2000
        try:
            run_agent(agent, _ctx(self.pid), repo_root=self.root)
        finally:
            runner_module.DEFAULT_FEED_BUDGET = original
        self.assertIn("truncated", agent.last_ctx.feed_context.lower())
        self.assertTrue(agent.last_ctx.feed_truncated)


class TestRunnerOnProjectWithNoFeed(unittest.TestCase):
    """A project without an activity.jsonl yet must not break the runner."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="runner_no_feed_"))
        self.pid = "PROJ-004-test-nf"
        _seed_project(self.root, self.pid)  # no items

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_empty_feed_context_passed_through(self):
        agent = StubAgent()
        run_agent(agent, _ctx(self.pid), repo_root=self.root)
        # dispatch_id assigned even with empty feed
        self.assertTrue(agent.last_ctx.dispatch_id)
        # feed_context empty, feed_snapshot_at set (the read still ran)
        # We allow either empty or a "no items" block — both are correct
        self.assertFalse("first comment" in agent.last_ctx.feed_context)


if __name__ == "__main__":
    unittest.main()
