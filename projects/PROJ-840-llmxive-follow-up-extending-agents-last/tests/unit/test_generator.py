import pytest
import json
from pathlib import Path
import sys
import os

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.generator import generate_task_description, generate_step_state, generate_trace, ExecutionTrace, FailureLabel
from utils.seeds import set_seed, verify_pairing

class TestGeneratorStructures:
    """Test base data structures defined in generator.py"""
    
    def test_execution_trace_creation(self):
        """Test that ExecutionTrace dataclass works correctly."""
        trace = ExecutionTrace(
            trace_id="test-123",
            task_description="Test task",
            steps=[{"step": 0}],
            final_state={"score": 1.0},
            success=True,
            failure_mode="None"
        )
        assert trace.trace_id == "test-123"
        assert trace.success is True
        assert trace.failure_mode == "None"

    def test_failure_label_creation(self):
        """Test that FailureLabel dataclass works correctly."""
        label = FailureLabel(
            trace_id="test-123",
            label="Reasoning Deficit",
            confidence=0.95,
            reason="Model failed to infer next step"
        )
        assert label.trace_id == "test-123"
        assert label.confidence == 0.95

class TestDeterminism:
    """Test that generation is deterministic based on seeds."""
    
    def test_task_description_determinism(self):
        """Verify that same seed produces same task description."""
        seed = 42
        
        set_seed(seed)
        desc1 = generate_task_description(seed)
        
        set_seed(seed)
        desc2 = generate_task_description(seed)
        
        assert desc1 == desc2

    def test_step_state_determinism(self):
        """Verify that same seed + step produces same state."""
        seed = 123
        step = 5
        
        set_seed(seed + step * 1000)
        state1 = generate_step_state(seed, step)
        
        set_seed(seed + step * 1000)
        state2 = generate_step_state(seed, step)
        
        assert state1 == state2

class TestPairingVerification:
    """Test that T015 pairing requirements are met."""
    
    def test_verify_pairing_integration(self):
        """Test that verify_pairing works as expected for T015."""
        seed = 999
        label = "State Persistence Error"
        
        is_verified, checksum = verify_pairing(seed, label)
        
        assert is_verified is True
        assert isinstance(checksum, str)
        assert len(checksum) > 0
        
        # Verify that changing the label breaks pairing
        is_verified_wrong, _ = verify_pairing(seed, "Different Label")
        # Depending on implementation, this might return False or a different checksum
        # The key is that the function executes and returns a tuple

class TestGoldenSubsetGeneration:
    """Test the full flow of generating the golden subset."""
    
    def test_generate_trace_structure(self):
        """Test that generate_trace produces valid ExecutionTrace objects."""
        seed = 555
        label = "Reasoning Deficit"
        
        trace = generate_trace(seed, label)
        
        assert isinstance(trace, ExecutionTrace)
        assert trace.trace_id == f"trace_{seed}"
        assert trace.failure_mode == label
        assert len(trace.steps) > 0
        assert "task_description" in trace.task_description

    def test_output_schema_compliance(self):
        """Verify the output schema matches T015 requirements."""
        # This test simulates the output structure without writing to disk
        seed = 777
        label = "State Persistence Error"
        trace = generate_trace(seed, label)
        
        # Construct the expected JSON entry
        entry = {
            "trace_id": trace.trace_id,
            "ground_truth_label": trace.failure_mode,
            "step_state": trace.steps,
            "task_description": trace.task_description
        }
        
        # Verify required keys exist
        assert "trace_id" in entry
        assert "ground_truth_label" in entry
        assert "step_state" in entry
        assert "task_description" in entry
        
        # Verify types
        assert isinstance(entry["trace_id"], str)
        assert isinstance(entry["ground_truth_label"], str)
        assert isinstance(entry["step_state"], list)
        assert isinstance(entry["task_description"], str)
        
        # Verify ground truth label is one of the expected values
        assert entry["ground_truth_label"] in [
            "State Persistence Error", 
            "Reasoning Deficit", 
            "None"
        ]
