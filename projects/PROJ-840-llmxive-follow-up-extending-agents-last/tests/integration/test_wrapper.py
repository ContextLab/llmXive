"""
Integration tests for the Context-Checkpointing Wrapper (T019).

These tests verify that the wrapper correctly:
1. Initializes with the correct interval N.
2. Triggers a checkpoint at the correct step counts.
3. Compresses context and injects summaries.
4. Produces valid output data.
"""
import json
import os
import sys
from pathlib import Path
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.intervention.wrapper import ContextCheckpointWrapper, run_intervention

class TestContextCheckpointWrapper:
    """Tests for the ContextCheckpointWrapper class."""

    def test_initialization_default_interval(self):
        """Test wrapper initializes with default interval if not specified."""
        wrapper = ContextCheckpointWrapper()
        assert wrapper.interval_n == 5  # Default defined in wrapper

    def test_initialization_custom_interval(self):
        """Test wrapper initializes with custom interval."""
        wrapper = ContextCheckpointWrapper(interval_n=3)
        assert wrapper.interval_n == 3

    def test_should_checkpoint_logic(self):
        """Test the logic for determining when to checkpoint."""
        wrapper = ContextCheckpointWrapper(interval_n=3)
        
        # Steps 1, 2 should not trigger
        wrapper.step_count = 1
        assert not wrapper.should_checkpoint()
        
        wrapper.step_count = 2
        assert not wrapper.should_checkpoint()
        
        # Step 3 should trigger
        wrapper.step_count = 3
        assert wrapper.should_checkpoint()
        
        # Step 4 should not
        wrapper.step_count = 4
        assert not wrapper.should_checkpoint()
        
        # Step 6 should trigger
        wrapper.step_count = 6
        assert wrapper.should_checkpoint()

    def test_compress_context(self):
        """Test context compression heuristic."""
        wrapper = ContextCheckpointWrapper()
        history = [
            {"step_id": 1, "action": "move", "state": {"x": 1, "y": 2}},
            {"step_id": 2, "action": "rotate", "state": {"x": 1, "y": 2, "rot": 90}},
            {"step_id": 3, "action": "grasp", "state": {"x": 1, "y": 2, "rot": 90, "held": True}}
        ]
        
        summary = wrapper._compress_context(history)
        
        assert isinstance(summary, str)
        assert "Step 1" in summary
        assert "Step 2" in summary
        assert "Step 3" in summary
        assert "move" in summary
        assert "grasp" in summary

    def test_inject_summary(self):
        """Test that summary is injected into context."""
        wrapper = ContextCheckpointWrapper()
        wrapper.state_summary = "Test Summary"
        context = [{"role": "user", "content": "Hello"}]
        
        updated_context = wrapper.inject_summary(context)
        
        assert len(updated_context) == 2
        assert updated_context[1]["role"] == "system"
        assert "Test Summary" in updated_context[1]["content"]
        assert "CONTEXT CHECKPOINT" in updated_context[1]["content"]

    def test_process_step_updates_log(self):
        """Test that process_step updates the execution log."""
        wrapper = ContextCheckpointWrapper(interval_n=2)
        history = []
        step_data = {"action": "test"}
        
        # Process step 1
        wrapper.process_step(step_data, history)
        log = wrapper.get_execution_log()
        assert len(log) == 1
        assert log[0]["step"] == 1
        assert not log[0]["checkpointed"]
        
        # Process step 2 (should checkpoint)
        wrapper.process_step(step_data, history)
        log = wrapper.get_execution_log()
        assert len(log) == 2
        assert log[1]["step"] == 2
        assert log[1]["checkpointed"]

class TestRunIntervention:
    """Tests for the run_intervention function."""

    def test_run_intervention_creates_output(self, tmp_path):
        """Test that run_intervention produces a valid result dictionary."""
        # Mock task data
        task_data = {
            "trace_id": "test_001",
            "task_description": "Test task for intervention",
            "max_steps": 10,
            "initial_state": {"start": True}
        }
        
        result = run_intervention(task_data, interval_n=2)
        
        assert isinstance(result, dict)
        assert "task_id" in result
        assert "passed" in result
        assert "checkpoints_triggered" in result
        assert "execution_log" in result
        assert result["task_id"] == "test_001"
        
        # Verify checkpoint logic
        # With 10 steps and interval 2, we expect checkpoints at 2, 4, 6, 8, 10
        # But the loop breaks early if 'success' is found.
        # In our mock, success happens at step > 5, so steps 1-6 run.
        # Checkpoints at 2, 4, 6.
        assert result["checkpoints_triggered"] >= 2

    def test_run_intervention_with_golden_data_structure(self):
        """Test that the function handles the expected golden subset schema."""
        # Simulate a task from data/raw/golden_subset.json
        task_data = {
            "trace_id": "gold_123",
            "ground_truth_label": "State Persistence Error",
            "step_state": {"x": 1},
            "task_description": "Complete the task successfully",
            "max_steps": 5,
            "initial_state": {}
        }
        
        result = run_intervention(task_data, interval_n=5)
        
        assert result["task_id"] == "gold_123"
        assert "execution_log" in result
        # With 5 steps and interval 5, one checkpoint at step 5
        assert result["checkpoints_triggered"] == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])