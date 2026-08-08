"""
Integration tests for the evaluation runner (T027).
Verifies that the runner executes multiple trials and calculates mean success probability.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from src.evaluation.runner import execute_evaluation_loop, NUM_TRIALS

@pytest.fixture
def mock_tasks():
    """Create mock task definitions for testing."""
    return [
        {
            "name": "test_task_1",
            "type": "alfworld",
            "config": {
                "description": "Pick up the apple from the table and put it in the microwave",
                "k": 3,
                "initial_state": {"room": "kitchen", "objects": ["apple", "table", "microwave"]}
            },
            "ground_truth_adapter": "data/processed/alfworld_apple.npz"
        },
        {
            "name": "test_task_2",
            "type": "searchqa",
            "config": {
                "description": "Who was the president of the United States in 2000?",
                "k": 3,
                "initial_state": {"query": "US president 2000"}
            },
            "ground_truth_adapter": "data/processed/searchqa_bush.npz"
        }
    ]

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_execute_evaluation_loop_calculates_mean_success_rate(mock_tasks, temp_output_dir):
    """
    Test that the evaluation loop executes NUM_TRIALS runs per task
    and correctly calculates the mean success probability.
    """
    # Note: In a real test, we would mock the environment and model loading
    # to avoid actual inference. Here we test the structure and logic.
    
    # This test verifies the loop structure and result calculation
    # Since we can't run actual inference in this test environment,
    # we verify the code structure and expected output format
    
    # Mock the run_single_trial function to return deterministic results
    import src.evaluation.runner as runner_module
    
    original_run_trial = runner_module.run_single_trial
    
    def mock_run_single_trial(task_name, env_type, adapter_path, base_model_path, task_config):
        # Return deterministic success/failure for testing
        # Task 1: 3 successes out of 5 trials (60% success rate)
        # Task 2: 4 successes out of 5 trials (80% success rate)
        if "test_task_1" in task_name:
            trial_id = task_config.get("_trial_id", 0)
            return trial_id < 3, 1.0, ""  # First 3 trials succeed
        else:
            trial_id = task_config.get("_trial_id", 0)
            return trial_id < 4, 1.0, ""  # First 4 trials succeed
    
    # Monkey patch for testing
    runner_module.run_single_trial = mock_run_single_trial
    
    try:
        results = execute_evaluation_loop(
            tasks=mock_tasks,
            base_model_path="/fake/path.gguf",
            output_dir=temp_output_dir,
            k_values=[1, 3, 5]
        )
        
        # Verify results structure
        assert "tasks" in results
        assert "summary" in results
        assert "sensitivity_analysis" in results
        
        # Verify each task has the expected number of trials
        for task_name, task_results in results["tasks"].items():
            assert "trials" in task_results
            assert len(task_results["trials"]) == NUM_TRIALS
            assert "success_count" in task_results
            assert "failure_count" in task_results
            assert "mean_success_rate" in task_results
            assert "mean_latency" in task_results
        
        # Verify mean success rate calculation
        # Task 1: 3/5 = 0.6
        assert abs(results["tasks"]["test_task_1"]["mean_success_rate"] - 0.6) < 1e-6
        # Task 2: 4/5 = 0.8
        assert abs(results["tasks"]["test_task_2"]["mean_success_rate"] - 0.8) < 1e-6
        
        # Verify summary statistics
        assert results["summary"]["total_tasks"] == 2
        assert results["summary"]["num_trials_per_task"] == NUM_TRIALS
        # Overall success rate should be (0.6 + 0.8) / 2 = 0.7
        assert abs(results["summary"]["overall_success_rate"] - 0.7) < 1e-6
        
        # Verify results file was created
        results_file = Path(temp_output_dir) / "evaluation_results.json"
        assert results_file.exists()
        
        # Verify JSON content
        with open(results_file, 'r') as f:
            saved_results = json.load(f)
        assert saved_results == results
        
    finally:
        # Restore original function
        runner_module.run_single_trial = original_run_trial

def test_sensitivity_analysis_with_multiple_k_values(mock_tasks, temp_output_dir):
    """
    Test that sensitivity analysis is performed for different k values.
    """
    import src.evaluation.runner as runner_module
    
    original_run_trial = runner_module.run_single_trial
    
    def mock_run_single_trial(task_name, env_type, adapter_path, base_model_path, task_config):
        # Return success for all trials in sensitivity analysis
        return True, 1.0, ""
    
    runner_module.run_single_trial = mock_run_single_trial
    
    try:
        results = execute_evaluation_loop(
            tasks=mock_tasks,
            base_model_path="/fake/path.gguf",
            output_dir=temp_output_dir,
            k_values=[1, 3, 5]
        )
        
        # Verify sensitivity analysis results
        assert "sensitivity_analysis" in results
        assert "k_1" in results["sensitivity_analysis"]
        assert "k_3" in results["sensitivity_analysis"]
        assert "k_5" in results["sensitivity_analysis"]
        
        for k_key, k_result in results["sensitivity_analysis"].items():
            assert "mean_success_rate" in k_result
            assert "task_count" in k_result
            assert k_result["task_count"] == len(mock_tasks)
            assert k_result["mean_success_rate"] == 1.0  # All succeeded in mock
        
    finally:
        runner_module.run_single_trial = original_run_trial

def test_memory_threshold_check():
    """
    Test that memory threshold check is implemented.
    """
    from src.evaluation.runner import check_memory_usage, MEMORY_THRESHOLD_GB
    
    # This test just verifies the function exists and returns a float
    mem_usage = check_memory_usage()
    assert isinstance(mem_usage, float)
    assert mem_usage >= 0.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
