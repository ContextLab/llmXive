"""
Unit tests for A* planner logic.
"""
import pytest
import sys
from pathlib import Path

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.planner import AStarPlanner, ActionSequence, create_planner


class TestAStarPlanner:
    """Tests for the A* planner implementation."""

    def test_planner_initialization(self):
        """Verify AStarPlanner initializes correctly."""
        planner = AStarPlanner()
        assert planner is not None

    def test_create_planner_factory(self):
        """Verify create_planner returns an instance."""
        planner = create_planner()
        assert isinstance(planner, AStarPlanner)

    def test_action_sequence_dataclass(self):
        """Verify ActionSequence is a valid dataclass."""
        seq = ActionSequence(
            sub_goals=["grasp_cup", "move_to_table"],
            task_id="test_001"
        )
        assert len(seq.sub_goals) == 2
        assert seq.task_id == "test_001"
