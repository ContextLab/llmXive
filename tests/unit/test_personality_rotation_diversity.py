"""T014: per-project position diversity bias (spec 010, FR-006)."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from llmxive.agents.position_diversity import (
    DIVERSITY_THRESHOLD,
    diversity_hint_for,
    load_positions,
    record_position,
)


class TestPositionDiversity(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name) / "personality_rotation.yaml"

    def test_no_hint_when_no_prior(self) -> None:
        self.assertEqual(diversity_hint_for(self.state, "PROJ-001-foo"), "")

    def test_no_hint_below_threshold(self) -> None:
        record_position(self.state, "PROJ-001-foo", "lean_against")
        record_position(self.state, "PROJ-001-foo", "lean_against")
        self.assertEqual(diversity_hint_for(self.state, "PROJ-001-foo"), "")

    def test_hint_when_three_consecutive_same(self) -> None:
        for _ in range(DIVERSITY_THRESHOLD):
            record_position(self.state, "PROJ-001-foo", "lean_against")
        hint = diversity_hint_for(self.state, "PROJ-001-foo")
        self.assertIn("lean_against", hint)
        self.assertIn("Prior contributors", hint)

    def test_no_hint_when_recent_mixed(self) -> None:
        record_position(self.state, "PROJ-001-foo", "lean_against")
        record_position(self.state, "PROJ-001-foo", "lean_toward")
        record_position(self.state, "PROJ-001-foo", "lean_against")
        self.assertEqual(diversity_hint_for(self.state, "PROJ-001-foo"), "")

    def test_per_project_isolation(self) -> None:
        for _ in range(DIVERSITY_THRESHOLD):
            record_position(self.state, "PROJ-001-foo", "lean_against")
        # Different project — no hint
        self.assertEqual(diversity_hint_for(self.state, "PROJ-002-bar"), "")

    def test_rolling_window(self) -> None:
        # Add many entries; load_positions should return at most MAX_RETAINED_POSITIONS
        from llmxive.agents.position_diversity import MAX_RETAINED_POSITIONS

        for i in range(MAX_RETAINED_POSITIONS + 5):
            record_position(self.state, "PROJ-001-foo", "lean_toward")
        positions = load_positions(self.state)["PROJ-001-foo"]
        self.assertEqual(len(positions), MAX_RETAINED_POSITIONS)

    def test_missing_state_file_returns_empty(self) -> None:
        # Note: load_positions called before any record_position
        self.assertEqual(load_positions(self.state), {})

    def test_record_empty_args_noop(self) -> None:
        record_position(self.state, "", "lean_toward")
        record_position(self.state, "PROJ-001", "")
        self.assertEqual(load_positions(self.state), {})


if __name__ == "__main__":
    unittest.main()
