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


def test_activity_severity_classifies_soft_vs_hard():
    """The feed must distinguish EXPECTED pipeline mechanics (a convergence
    kickback, a librarian hold, an abstain) from genuine ERRORS (crashes,
    malformed output, backend failures), so a healthy converging pipeline does
    not read as a wall of red failures. The dashboard renders soft amber, hard red."""
    from llmxive.web_data import _activity_severity

    assert _activity_severity("success", "") == "ok"
    assert _activity_severity("committed", "") == "ok"
    # Expected, self-healing mechanics → soft.
    assert _activity_severity("abstained", "") == "soft"
    assert _activity_severity("librarian_held", "") == "soft"
    assert _activity_severity("triage_rejected_advanced_as_abstain", "") == "soft"
    assert _activity_severity(
        "failed", "StagePanelKickback: plan panel did not converge: 9 concern(s)"
    ) == "soft"
    # Genuine errors → hard.
    assert _activity_severity(
        "failed", "StagePanelEscalation: tasks panel engine failure: RuntimeError"
    ) == "hard"
    assert _activity_severity("failed", "ValueError: round 1 already recorded") == "hard"
    assert _activity_severity("malformed_response", "") == "hard"
    assert _activity_severity("model_error", "") == "hard"


def test_recent_activity_rows_carry_severity_and_reason(tmp_path: Path):
    """Each activity row exposes a `severity` (ok|soft|hard) and a truncated
    `failure_reason` so the UI can colour-code without re-deriving on the client."""
    month = tmp_path / "state" / "run-log" / "2026-06"
    month.mkdir(parents=True)
    rows = [
        {"agent_name": "planner", "project_id": "PROJ-1", "outcome": "failed",
         "failure_reason": "StagePanelKickback: plan panel did not converge: 5 concern(s)",
         "started_at": "2026-06-01T00:00:00Z", "ended_at": "2026-06-01T00:01:00Z"},
        {"agent_name": "reviewer", "project_id": "PROJ-1", "outcome": "failed",
         "failure_reason": "RuntimeError: boom",
         "started_at": "2026-06-01T00:02:00Z", "ended_at": "2026-06-01T00:03:00Z"},
        {"agent_name": "brainstormer", "project_id": "PROJ-1", "outcome": "committed",
         "started_at": "2026-06-01T00:04:00Z", "ended_at": "2026-06-01T00:05:00Z"},
    ]
    (month / "a.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows), encoding="utf-8"
    )
    out = _recent_activity(tmp_path)
    by_outcome = {(r["agent"], r["outcome"]): r for r in out}
    assert by_outcome[("planner", "failed")]["severity"] == "soft"
    assert by_outcome[("reviewer", "failed")]["severity"] == "hard"
    assert by_outcome[("brainstormer", "committed")]["severity"] == "ok"
    assert "StagePanelKickback" in by_outcome[("planner", "failed")]["failure_reason"]
