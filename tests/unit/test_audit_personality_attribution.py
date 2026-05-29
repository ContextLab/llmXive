"""Tests for scripts/audit_personality_attribution.py (T066, SC-004).

Drives the script's :func:`audit` function over a tmp-dir fixture run-log
containing both conformant and non-conformant entries; asserts the script
reports the right counts.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

# Load the script as a module by file path.
SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "audit_personality_attribution.py"
spec = importlib.util.spec_from_file_location("audit_mod", SCRIPT)
audit_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_mod)


def _write_jsonl(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")


class TestAudit:
    def test_conformant_entries_zero_violations(self, tmp_path: Path) -> None:
        run_log = tmp_path / "state" / "run-log" / "2026-05"
        _write_jsonl(run_log / "run1.jsonl", [
            {
                "agent_name": "personality",
                "model_name": "qwen.qwen3.5-122b",
                "model_kind": "personality_simulator",
                "personality_slug": "kahneman",
                "display_name": "Daniel Kahneman (simulated)",
                "outcome": "committed",
                "action": "comment",
            },
        ])
        n, viol, rows = audit_mod.audit(tmp_path / "state" / "run-log")
        assert n == 1
        assert viol == 0
        assert rows == []

    def test_wrong_model_flagged(self, tmp_path: Path) -> None:
        run_log = tmp_path / "state" / "run-log" / "2026-05"
        _write_jsonl(run_log / "run1.jsonl", [
            {
                "agent_name": "personality",
                "model_name": "gpt-4",
                "model_kind": "personality_simulator",
                "personality_slug": "kahneman",
                "display_name": "Daniel Kahneman (simulated)",
                "outcome": "committed",
            },
        ])
        _n, viol, rows = audit_mod.audit(tmp_path / "state" / "run-log")
        assert viol == 1
        assert "model_name" in rows[0]["problems"]

    def test_missing_simulated_suffix_flagged(self, tmp_path: Path) -> None:
        run_log = tmp_path / "state" / "run-log" / "2026-05"
        _write_jsonl(run_log / "run1.jsonl", [
            {
                "agent_name": "personality",
                "model_name": "qwen.qwen3.5-122b",
                "model_kind": "personality_simulator",
                "personality_slug": "kahneman",
                "display_name": "Daniel Kahneman",       # ← suffix MISSING
                "outcome": "committed",
            },
        ])
        _n, viol, rows = audit_mod.audit(tmp_path / "state" / "run-log")
        assert viol == 1
        assert "(simulated)" in rows[0]["problems"]

    def test_non_personality_entries_ignored(self, tmp_path: Path) -> None:
        run_log = tmp_path / "state" / "run-log" / "2026-05"
        _write_jsonl(run_log / "run1.jsonl", [
            {"agent_name": "brainstorm", "model_name": "qwen", "outcome": "ok"},
            {"agent_name": "librarian", "model_name": "qwen", "outcome": "ok"},
        ])
        n, viol, _ = audit_mod.audit(tmp_path / "state" / "run-log")
        assert n == 0
        assert viol == 0

    def test_tick_level_failure_without_slug_not_flagged(self, tmp_path: Path) -> None:
        """rate_limited / model_error before persona selection legitimately
        has null personality_slug + null display_name. Audit must not flag."""
        run_log = tmp_path / "state" / "run-log" / "2026-05"
        _write_jsonl(run_log / "run1.jsonl", [
            {
                "agent_name": "personality",
                "model_name": "qwen.qwen3.5-122b",
                "model_kind": "personality_simulator",
                "personality_slug": None,
                "display_name": None,
                "outcome": "rate_limited",
            },
        ])
        n, viol, _ = audit_mod.audit(tmp_path / "state" / "run-log")
        assert n == 1
        assert viol == 0

    def test_missing_run_log_dir_returns_zero(self, tmp_path: Path) -> None:
        n, viol, _ = audit_mod.audit(tmp_path / "no-such-dir")
        assert n == 0
        assert viol == 0
