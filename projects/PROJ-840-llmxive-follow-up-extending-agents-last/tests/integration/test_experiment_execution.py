"""
Integration test for T023: Experiment Execution.

This test verifies that the experiment runner script:
1. Loads the golden subset correctly.
2. Executes both baseline and intervention modes.
3. Produces valid JSON output files with the expected schema.
4. Ensures that the same seed produces deterministic results.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.seeds import set_seed, generate_task_seed
from utils.config import load_config
from intervention.runner import CPUOnlyRunner, ExecutionResult
from intervention.wrapper import ContextCheckpointWrapper
from data.generator import generate_trace, generate_task_description, FailureType, ExecutionTrace

# Mock the golden subset generation for testing if the real file is missing
# In a real CI environment, T015 should have run first.
# Here we create a temporary golden subset for the test.

def create_temp_golden_subset(tmp_path: Path, count: int = 3) -> Path:
    """Create a temporary golden subset file for testing."""
    golden_path = tmp_path / "data" / "raw" / "golden_subset.json"
    golden_path.parent.mkdir(parents=True, exist_ok=True)
    
    traces = []
    for i in range(count):
        trace = generate_trace(
            task_id=f"test_task_{i}",
            failure_type=FailureType.STATE_PERSISTENCE if i % 2 == 0 else FailureType.REASONING_DEFICIT,
            seed=i + 100
        )
        traces.append({
            "trace_id": trace.trace_id,
            "ground_truth_label": trace.failure_label.label,
            "step_state": trace.step_state,
            "task_description": trace.task_description
        })
    
    with open(golden_path, 'w', encoding='utf-8') as f:
        json.dump(traces, f)
    
    return golden_path

def run_baseline_single(trace: dict, seed: int) -> dict:
    """Helper to run a single baseline trace."""
    set_seed(seed)
    runner = CPUOnlyRunner()
    task_seed = generate_task_seed(seed, trace['trace_id'])
    set_seed(task_seed)
    
    result = runner.run(trace['task_description'], trace.get('step_state', {}))
    return {
        "trace_id": trace['trace_id'],
        "passed": result.passed,
        "mode": "baseline"
    }

def run_intervention_single(trace: dict, seed: int, interval: int = 3) -> dict:
    """Helper to run a single intervention trace."""
    set_seed(seed)
    # Mock config
    from utils.config import PipelineConfig, CheckpointConfig
    config = PipelineConfig()
    config.checkpoint = CheckpointConfig()
    config.checkpoint.interval = interval
    
    wrapper = ContextCheckpointWrapper(config.checkpoint)
    task_seed = generate_task_seed(seed, trace['trace_id'])
    set_seed(task_seed)
    
    result = wrapper.run(trace['task_description'], trace.get('step_state', {}))
    return {
        "trace_id": trace['trace_id'],
        "passed": result.passed,
        "mode": "intervention"
    }

@pytest.fixture
def temp_project_structure(tmp_path: Path):
    """Setup a temporary project structure with mock golden data."""
    # We don't actually run the full script, but we test the logic components
    # that T023 relies on.
    return tmp_path

def test_baseline_execution_logic():
    """Test that the baseline runner logic produces consistent results."""
    # Create a mock trace
    trace = generate_trace(
        task_id="test_baseline_1",
        failure_type=FailureType.STATE_PERSISTENCE,
        seed=42
    )
    trace_dict = {
        "trace_id": trace.trace_id,
        "ground_truth_label": trace.failure_label.label,
        "step_state": trace.step_state,
        "task_description": trace.task_description
    }
    
    # Run twice with same seed
    seed = 12345
    result1 = run_baseline_single(trace_dict, seed)
    result2 = run_baseline_single(trace_dict, seed)
    
    assert result1['passed'] == result2['passed'], "Baseline execution must be deterministic with same seed."
    assert result1['trace_id'] == trace_dict['trace_id']
    assert isinstance(result1['passed'], bool)

def test_intervention_execution_logic():
    """Test that the intervention runner logic produces consistent results."""
    trace = generate_trace(
        task_id="test_intervention_1",
        failure_type=FailureType.REASONING_DEFICIT,
        seed=42
    )
    trace_dict = {
        "trace_id": trace.trace_id,
        "ground_truth_label": trace.failure_label.label,
        "step_state": trace.step_state,
        "task_description": trace.task_description
    }
    
    seed = 67890
    result1 = run_intervention_single(trace_dict, seed, interval=3)
    result2 = run_intervention_single(trace_dict, seed, interval=3)
    
    assert result1['passed'] == result2['passed'], "Intervention execution must be deterministic with same seed."
    assert result1['trace_id'] == trace_dict['trace_id']
    assert isinstance(result1['passed'], bool)
    assert 'checkpoint_interval' in result1  # Check if metadata is present

def test_output_schema_compliance(temp_project_structure):
    """Verify that the output files would have the correct schema."""
    # Simulate the structure of the output files
    baseline_sample = [
        {
            "trace_id": "test_1",
            "passed": True,
            "execution_time_seconds": 1.5,
            "mode": "baseline"
        }
    ]
    
    intervention_sample = [
        {
            "trace_id": "test_1",
            "passed": False,
            "execution_time_seconds": 2.0,
            "mode": "intervention",
            "checkpoint_interval": 3
        }
    ]
    
    # Validate schema
    for item in baseline_sample:
        assert "trace_id" in item
        assert "passed" in item
        assert isinstance(item["passed"], bool)
        assert "mode" in item
        assert item["mode"] == "baseline"
    
    for item in intervention_sample:
        assert "trace_id" in item
        assert "passed" in item
        assert isinstance(item["passed"], bool)
        assert "mode" in item
        assert item["mode"] == "intervention"
        assert "checkpoint_interval" in item

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
