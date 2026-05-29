"""Tests for `_recent_activity` cross-project aggregator (Activity tab).

Drives the function against tmp-dir fixture run-logs with multiple
projects + multiple agents (incl. simulated personality entries) and
asserts:

- Latest-first ordering by `ended_at`.
- ``limit`` truncation.
- Personality-specific fields (display_name, personality_slug, action,
  model_kind) flow through verbatim.
- Empty / missing run-log root returns an empty list (no crash).
- The function tolerates malformed JSONL lines (skips, doesn't error).
"""

from __future__ import annotations

import json
from pathlib import Path

from llmxive.web_data import _recent_activity


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")


def _entry(*, agent: str, project: str, ts: str, outcome: str = "success",
           **extra) -> dict:
    return {
        "agent_name": agent,
        "model_name": "qwen.qwen3.5-122b",
        "project_id": project,
        "started_at": ts,
        "ended_at": ts,
        "outcome": outcome,
        **extra,
    }


class TestRecentActivity:
    def test_empty_when_no_runlog_dir(self, tmp_path: Path) -> None:
        assert _recent_activity(tmp_path) == []

    def test_aggregates_across_projects(self, tmp_path: Path) -> None:
        _write_jsonl(tmp_path / "state" / "run-log" / "2026-05" / "a.jsonl", [
            _entry(agent="brainstorm", project="PROJ-001-foo", ts="2026-05-10T10:00:00+00:00"),
            _entry(agent="flesh_out",  project="PROJ-002-bar", ts="2026-05-10T11:00:00+00:00"),
        ])
        out = _recent_activity(tmp_path)
        assert len(out) == 2
        # newest first.
        assert out[0]["project_id"] == "PROJ-002-bar"
        assert out[1]["project_id"] == "PROJ-001-foo"

    def test_walks_multiple_months_newest_first(self, tmp_path: Path) -> None:
        _write_jsonl(tmp_path / "state" / "run-log" / "2026-04" / "a.jsonl", [
            _entry(agent="implementer", project="PROJ-001-foo", ts="2026-04-15T10:00:00+00:00"),
        ])
        _write_jsonl(tmp_path / "state" / "run-log" / "2026-05" / "a.jsonl", [
            _entry(agent="flesh_out", project="PROJ-002-bar", ts="2026-05-10T10:00:00+00:00"),
        ])
        out = _recent_activity(tmp_path)
        assert out[0]["project_id"] == "PROJ-002-bar"
        assert out[1]["project_id"] == "PROJ-001-foo"

    def test_truncates_to_limit(self, tmp_path: Path) -> None:
        # Write 100 entries; default limit is 60.
        entries = [
            _entry(agent="brainstorm", project=f"PROJ-{i:03d}-x",
                   ts=f"2026-05-10T{i % 24:02d}:00:00+00:00")
            for i in range(100)
        ]
        _write_jsonl(tmp_path / "state" / "run-log" / "2026-05" / "a.jsonl", entries)
        out = _recent_activity(tmp_path, limit=60)
        assert len(out) == 60

    def test_personality_fields_propagated(self, tmp_path: Path) -> None:
        _write_jsonl(tmp_path / "state" / "run-log" / "2026-05" / "a.jsonl", [
            {
                "agent_name": "personality",
                "model_name": "qwen.qwen3.5-122b",
                "model_kind": "personality_simulator",
                "personality_slug": "daniel-kahneman",
                "display_name": "Daniel Kahneman (simulated)",
                "project_id": "PROJ-001-foo",
                "started_at": "2026-05-10T10:00:00+00:00",
                "ended_at": "2026-05-10T10:00:11+00:00",
                "outcome": "committed",
                "action": "comment",
            },
        ])
        out = _recent_activity(tmp_path)
        assert len(out) == 1
        row = out[0]
        assert row["display_name"] == "Daniel Kahneman (simulated)"
        assert row["personality_slug"] == "daniel-kahneman"
        assert row["model_kind"] == "personality_simulator"
        assert row["action"] == "comment"
        assert row["outcome"] == "committed"

    def test_skips_malformed_lines(self, tmp_path: Path) -> None:
        log = tmp_path / "state" / "run-log" / "2026-05" / "a.jsonl"
        log.parent.mkdir(parents=True)
        log.write_text(
            json.dumps(_entry(agent="brainstorm", project="PROJ-001-x", ts="2026-05-10T10:00:00+00:00")) + "\n"
            + "this is not json\n"
            + json.dumps(_entry(agent="flesh_out", project="PROJ-002-y", ts="2026-05-10T11:00:00+00:00")) + "\n",
            encoding="utf-8",
        )
        out = _recent_activity(tmp_path)
        # Two valid entries, one bad line skipped.
        assert len(out) == 2

    def test_duration_computed_from_timestamps(self, tmp_path: Path) -> None:
        _write_jsonl(tmp_path / "state" / "run-log" / "2026-05" / "a.jsonl", [
            {
                "agent_name": "implementer",
                "model_name": "qwen.qwen3.5-122b",
                "project_id": "PROJ-001-foo",
                "started_at": "2026-05-10T10:00:00+00:00",
                "ended_at": "2026-05-10T10:00:42+00:00",
                "outcome": "success",
            },
        ])
        out = _recent_activity(tmp_path)
        assert out[0]["duration_s"] == 42.0
