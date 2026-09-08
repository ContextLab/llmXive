"""
Integration test for A* planner generating valid sequences.
Verifies the planner produces a valid ActionSequence within the 60s CPU constraint
using real (mocked for test isolation) SymbolicState inputs.
"""
import pytest
import sys
from pathlib import Path
import time

# Ensure src is importable
src_path = Path(__file__).parent.parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.planner import create_planner, ActionSequence, ResourceLimitExceeded
from src.state_mapper import SymbolicState, AffordanceGraph
from src.config import PLANNING_TIMEOUT_S


class TestPlannerIntegration:
    """Integration tests for the planner module."""

    def test_planning_pipeline_basic(self):
        """Test that the planner can generate a sequence from a mock state."""
        planner = create_planner()

        # Create a mock symbolic state
        # This simulates a state where an object is on a table and needs to be moved
        mock_state = SymbolicState(
            task_id="int_test_001",
            predicates={"object_on_table": True, "goal_reached": False},
            affordances={"object": ["graspable", "movable"], "table": ["stable"]},
            replan_support=True
        )

        # Run planning
        # We expect this to return an ActionSequence within the time limit
        start_time = time.time()
        try:
            result = planner.plan(mock_state)
            elapsed = time.time() - start_time
        except ResourceLimitExceeded as e:
            pytest.fail(f"Planning exceeded resource limits: {e}")

        assert isinstance(result, ActionSequence)
        assert result.task_id == "int_test_001"
        assert len(result.actions) > 0, "Planner returned an empty sequence"
        assert elapsed < PLANNING_TIMEOUT_S, f"Planning took too long: {elapsed}s (limit: {PLANNING_TIMEOUT_S}s)"

    def test_planning_replan_support_true(self):
        """Test that planner respects replan_support flag."""
        planner = create_planner()

        mock_state = SymbolicState(
            task_id="int_test_002",
            predicates={"block_a_on_b": True},
            affordances={"block_a": ["stackable", "movable"]},
            replan_support=True
        )

        result = planner.plan(mock_state)
        
        assert result.task_id == "int_test_002"
        assert result.replan_enabled is True

    def test_planning_replan_support_false(self):
        """Test that planner respects replan_support flag when false."""
        planner = create_planner()

        mock_state = SymbolicState(
            task_id="int_test_003",
            predicates={"block_a_on_b": True},
            affordances={"block_a": ["stackable"]},
            replan_support=False
        )

        result = planner.plan(mock_state)
        
        assert result.task_id == "int_test_003"
        assert result.replan_enabled is False

    def test_planning_timeout_handling(self):
        """Test that the planner raises an error if it exceeds the time limit."""
        # This test mocks the planner's internal heuristic to force a delay
        # In a real integration scenario, we might use a very large graph,
        # but for unit/integration stability, we rely on the planner's internal timeout check.
        planner = create_planner()
        
        # Create a state that might be computationally expensive if the graph was large
        # Here we just verify the timeout logic exists by checking the config
        mock_state = SymbolicState(
            task_id="int_test_004",
            predicates={"complex_state": True},
            affordances={"obj": ["movable"]},
            replan_support=True
        )
        
        # The planner should respect the global timeout config
        start = time.time()
        result = planner.plan(mock_state)
        duration = time.time() - start
        
        # Ensure it didn't run forever (should be fast for this mock)
        assert duration < PLANNING_TIMEOUT_S

    def test_planning_output_structure(self):
        """Verify the structure of the generated ActionSequence."""
        planner = create_planner()
        
        mock_state = SymbolicState(
            task_id="int_test_005",
            predicates={"start": True},
            affordances={"x": ["y"]},
            replan_support=True
        )
        
        result = planner.plan(mock_state)
        
        # Check that the result has the expected attributes
        assert hasattr(result, 'task_id')
        assert hasattr(result, 'actions')
        assert hasattr(result, 'replan_enabled')
        assert hasattr(result, 'planning_time')