"""Rotation-state YAML IO tests (spec 008 Phase 2 / data-model.md E2 / FR-003).

Pure-Python — drives :func:`personality.load_rotation_state` and
:func:`personality.write_rotation_state` against tmp-dir fixtures covering
the round-trip, every recovery path, and the 200-entry history-truncation
rule.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.agents import personality as p


class TestRotationStateLoad:
    def test_missing_file_returns_default(self, tmp_path: Path) -> None:
        state = p.load_rotation_state(tmp_path / "missing.yaml")
        assert state.last_used is None
        assert state.last_outcome == p.OUTCOME_ABSTAINED
        assert state.history == []

    def test_corrupted_yaml_recovers_to_default(self, tmp_path: Path, caplog) -> None:
        bad = tmp_path / "rot.yaml"
        bad.write_text("not: valid: yaml: :", encoding="utf-8")
        state = p.load_rotation_state(bad)
        assert state.last_used is None
        assert state.last_outcome == p.OUTCOME_ABSTAINED

    def test_non_dict_yaml_recovers_to_default(self, tmp_path: Path) -> None:
        bad = tmp_path / "rot.yaml"
        bad.write_text("- just\n- a\n- list\n", encoding="utf-8")
        state = p.load_rotation_state(bad)
        assert state.last_used is None

    def test_missing_keys_filled_with_defaults(self, tmp_path: Path) -> None:
        partial = tmp_path / "rot.yaml"
        partial.write_text("last_used: kahneman\n", encoding="utf-8")
        state = p.load_rotation_state(partial)
        assert state.last_used == "kahneman"
        # Other fields filled from defaults.
        assert state.last_outcome  # non-empty
        assert state.history == []


class TestRotationStateWrite:
    def test_round_trip(self, tmp_path: Path) -> None:
        state = p.RotationState(
            last_used="daniel-kahneman",
            last_used_at="2026-05-14T08:30:12+00:00",
            last_outcome=p.OUTCOME_COMMITTED,
            history=[
                {"slug": "ada-lovelace",
                 "started_at": "2026-05-14T08:00:08+00:00",
                 "outcome": p.OUTCOME_COMMITTED,
                 "action": "comment"},
                {"slug": "daniel-kahneman",
                 "started_at": "2026-05-14T08:30:01+00:00",
                 "outcome": p.OUTCOME_COMMITTED,
                 "action": "contribute"},
            ],
        )
        path = tmp_path / "rot.yaml"
        p.write_rotation_state(state, path)
        reloaded = p.load_rotation_state(path)
        assert reloaded.last_used == state.last_used
        assert reloaded.last_used_at == state.last_used_at
        assert reloaded.last_outcome == state.last_outcome
        assert reloaded.history == state.history

    def test_history_truncated_at_limit(self, tmp_path: Path) -> None:
        # Build a state with 300 history entries; the writer should truncate
        # to the most recent HISTORY_LIMIT (200).
        big_history = [
            {"slug": f"persona-{i:03d}", "started_at": f"2026-01-01T{i % 24:02d}:00:00+00:00",
             "outcome": p.OUTCOME_COMMITTED, "action": "abstain"}
            for i in range(300)
        ]
        state = p.RotationState(
            last_used="persona-299",
            last_used_at="2026-01-02T00:00:00+00:00",
            last_outcome=p.OUTCOME_COMMITTED,
            history=big_history,
        )
        path = tmp_path / "rot.yaml"
        p.write_rotation_state(state, path)
        reloaded = p.load_rotation_state(path)
        assert len(reloaded.history) == p.HISTORY_LIMIT
        # The KEPT entries are the LAST 200 — newest survive.
        assert reloaded.history[0]["slug"] == "persona-100"
        assert reloaded.history[-1]["slug"] == "persona-299"

    def test_atomic_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        # Writer must mkdir(parents=True) so a fresh state/personality_rotation.yaml
        # can land even if state/ doesn't exist yet (first cron run).
        state = p.RotationState(
            last_used=None,
            last_used_at="2026-05-14T00:00:00+00:00",
            last_outcome=p.OUTCOME_ABSTAINED,
            history=[],
        )
        nested = tmp_path / "new-dir" / "rot.yaml"
        p.write_rotation_state(state, nested)
        assert nested.is_file()
        # Round-trip from the new location.
        reloaded = p.load_rotation_state(nested)
        assert reloaded.last_used is None
