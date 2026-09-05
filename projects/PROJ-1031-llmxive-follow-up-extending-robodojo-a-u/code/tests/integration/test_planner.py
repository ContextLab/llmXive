"""
Integration test for A* planner generating valid sequences.
"""
import pytest
import sys
from pathlib import Path
import time

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.planner import create_planner, ActionSequence
from src.state_mapper import SymbolicState


class TestPlannerIntegration:
    """Integration tests for the planner module."""

    def test_planning_pipeline_basic(self):
        """Test that the planner can generate a sequence from a mock state."""
        planner = create_planner()

        # Create a mock symbolic state
        mock_state = SymbolicState(
            task_id="int_test_001",
            predicates={"object_on_table": True},
            affordances={"object": ["graspable", "movable"]},
            replan_support=True
        )

        # Run planning (mocked graph logic inside planner)
        # We expect this to return an ActionSequence within the time limit
        start_time = time.time()
        result = planner.plan(mock_state)
        elapsed = time.time() - start_time

        assert isinstance(result, ActionSequence)
        assert result.task_id == "int_test_001"
        assert elapsed < 60.0, f"Planning took too long: {elapsed}s"
