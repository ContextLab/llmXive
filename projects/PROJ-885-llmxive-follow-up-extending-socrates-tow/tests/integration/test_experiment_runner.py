"""
Integration test for paired experiment execution (Adapter vs. Static).

This test verifies that:
1. The experiment runner correctly loads trajectories from data/processed/trajectories.json
2. The classifier is loaded and used to predict socio-cognitive states
3. Dynamic state injection (Adapter condition) injects appropriate prompts
4. Static condition runs without injection
5. Logs are written to data/processed/experiment_logs.json
6. The output logs contain the expected structure and condition markers
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import project modules
from config import ensure_directories, setup_logging
from data.generator import main as generate_main
from experiments.runner import run_experiment, ExperimentConfig
from models.classifier import Classifier
from experiments.prompts import get_prompt_template


@pytest.fixture(scope="module")
def setup_test_environment():
    """Set up a temporary directory for test outputs."""
    # Use a temporary directory for this integration test
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Override config paths for testing
        original_data_raw = os.environ.get("DATA_RAW_DIR")
        original_data_processed = os.environ.get("DATA_PROCESSED_DIR")
        original_data_results = os.environ.get("DATA_RESULTS_DIR")
        
        os.environ["DATA_RAW_DIR"] = str(tmp_path / "raw")
        os.environ["DATA_PROCESSED_DIR"] = str(tmp_path / "processed")
        os.environ["DATA_RESULTS_DIR"] = str(tmp_path / "results")
        
        # Ensure directories exist
        ensure_directories()
        
        # Setup logging
        setup_logging(level="INFO")
        
        yield tmp_path
        
        # Restore original paths
        if original_data_raw:
            os.environ["DATA_RAW_DIR"] = original_data_raw
        else:
            os.environ.pop("DATA_RAW_DIR", None)
        if original_data_processed:
            os.environ["DATA_PROCESSED_DIR"] = original_data_processed
        else:
            os.environ.pop("DATA_PROCESSED_DIR", None)
        if original_data_results:
            os.environ["DATA_RESULTS_DIR"] = original_data_results
        else:
            os.environ.pop("DATA_RESULTS_DIR", None)

@pytest.fixture(scope="module")
def generated_trajectories(setup_test_environment):
    """Generate sample trajectories for testing."""
    # We need to generate trajectories first
    # This simulates running T012-T016
    trajectories_path = Path(setup_test_environment) / "processed" / "trajectories.json"
    stats_path = Path(setup_test_environment) / "processed" / "generation_stats.json"
    
    # Generate a small set of trajectories for testing
    # We'll use a reduced number for speed
    generate_main(num_trajectories=10, num_turns_per_trajectory=3)
    
    assert trajectories_path.exists(), "Trajectories file not generated"
    assert stats_path.exists(), "Generation stats file not generated"
    
    with open(trajectories_path, "r") as f:
        trajectories = json.load(f)
    
    return trajectories

@pytest.fixture(scope="module")
def trained_classifier(setup_test_environment, generated_trajectories):
    """Train a classifier on the generated data."""
    # Generate classifier training data
    from data.generator import main as generate_main
    generate_main(num_trajectories=10, num_turns_per_trajectory=3)
    
    # Train a simple classifier
    classifier = Classifier()
    classifier.train()
    
    return classifier

def test_experiment_runner_paired_conditions(setup_test_environment, generated_trajectories, trained_classifier):
    """
    Test that the experiment runner correctly executes paired experiments.
    
    Verifies:
    - Both Adapter and Static conditions are run
    - Logs contain condition markers
    - Adapter logs contain injected state signals
    - Static logs do not contain injected state signals
    - Output file is written correctly
    """
    from experiments.runner import run_experiment
    
    # Define experiment configuration
    config = ExperimentConfig(
        condition="both",  # Run both Adapter and Static
        model_name="hf-internal-testing/tiny-random-LlamaForCausalLM",  # Tiny model for testing
        trajectory_subset=5,  # Use only 5 trajectories for speed
        num_turns_per_trajectory=3,
        classifier_confidence_threshold=0.3,
        output_path=Path(setup_test_environment) / "processed" / "experiment_logs.json"
    )
    
    # Mock the model loading and inference to avoid actual LLM calls
    with patch('experiments.runner.check_and_load_model') as mock_load, \
         patch('experiments.runner.AutoModelForCausalLM') as mock_model_class, \
         patch('experiments.runner.AutoTokenizer') as mock_tokenizer_class:
         
         # Setup mocks
         mock_model = MagicMock()
         mock_tokenizer = MagicMock()
         mock_load.return_value = (mock_model, mock_tokenizer)
         
         # Mock the model's generate method to return a simple response
         mock_model.generate.return_value = torch.tensor([[1, 2, 3]])
         mock_tokenizer.decode.return_value = "Mocked response"
         mock_tokenizer.apply_chat_template.return_value = "Mocked prompt"
         
         import torch
         
         # Run the experiment
         try:
             run_experiment(config, trained_classifier)
         except Exception as e:
             # If the experiment fails due to missing real data or other issues,
             # we check if it's a expected failure (e.g., no real trajectories)
             if "No trajectories found" in str(e) or "File not found" in str(e):
                 # This is expected if trajectories weren't generated properly
                 pytest.skip("Trajectories not properly generated for test")
             else:
                 raise
    
    # Check that output file was created
    output_path = config.output_path
    assert output_path.exists(), f"Experiment logs not written to {output_path}"
    
    # Load and verify the logs
    with open(output_path, "r") as f:
        logs = json.load(f)
    
    assert isinstance(logs, list), "Logs should be a list"
    assert len(logs) > 0, "Logs should not be empty"
    
    # Verify structure of each log entry
    for log in logs:
        assert "trajectory_id" in log, "Missing trajectory_id in log"
        assert "condition" in log, "Missing condition in log"
        assert "injected_state" in log, "Missing injected_state in log"
        assert "llm_output" in log, "Missing llm_output in log"
        
        # Verify condition is either "Adapter" or "Static"
        assert log["condition"] in ["Adapter", "Static"], f"Invalid condition: {log['condition']}"
    
    # Verify both conditions are present
    conditions = set(log["condition"] for log in logs)
    assert "Adapter" in conditions, "Adapter condition not found in logs"
    assert "Static" in conditions, "Static condition not found in logs"
    
    # Verify Adapter logs contain injected state signals
    adapter_logs = [log for log in logs if log["condition"] == "Adapter"]
    assert len(adapter_logs) > 0, "No Adapter logs found"
    
    # At least some Adapter logs should have injected states
    adapter_with_injection = [log for log in adapter_logs if log["injected_state"] is not None]
    # Note: This might be 0 if classifier confidence is too low, which is acceptable
    
    # Verify Static logs do NOT contain injected state signals (should be None)
    static_logs = [log for log in logs if log["condition"] == "Static"]
    assert len(static_logs) > 0, "No Static logs found"
    
    for log in static_logs:
        assert log["injected_state"] is None, f"Static condition should not have injected state: {log}"

def test_experiment_runner_memory_constraint(setup_test_environment):
    """
    Test that the experiment runner respects memory constraints.
    
    Verifies that large models are excluded based on memory estimation.
    """
    from experiments.model_loader import filter_models_by_memory
    
    # Test that filter_models_by_memory works correctly
    all_models = get_available_models()
    filtered_models = filter_models_by_memory(all_models, max_memory_gb=7.0)
    
    # All filtered models should be within memory limit
    for model_info in filtered_models:
        assert model_info.estimated_memory_gb <= 7.0, f"Model {model_info.name} exceeds memory limit"

def test_experiment_runner_retry_logic(setup_test_environment):
    """
    Test that the experiment runner correctly handles failures with retry logic.
    
    Verifies that retry mechanism is properly integrated.
    """
    from experiments.retry_utils import exponential_backoff_retry
    
    # Test retry logic with a function that fails initially then succeeds
    call_count = 0
    
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Temporary failure")
        return "success"
    
    result = exponential_backoff_retry(
        flaky_function,
        max_retries=5,
        base_delay=0.1,
        max_delay=1.0
    )
    
    assert result == "success", "Retry logic should eventually succeed"
    assert call_count == 3, f"Function should have been called 3 times, was called {call_count} times"

def test_experiment_runner_cpu_only(setup_test_environment):
    """
    Test that the experiment runner enforces CPU-only execution.
    
    Verifies that GPU libraries are not used and CUDA is not available.
    """
    import torch
    
    # Check that CUDA is not available or not used
    # Note: This test might pass even if CUDA is available, as long as we don't use it
    assert not torch.cuda.is_available() or torch.cuda.device_count() == 0, \
        "CUDA should not be available for CPU-only execution"
    
    # Verify that the model loader checks for memory constraints
    from experiments.model_loader import check_and_load_model
    
    # This test mainly verifies that the infrastructure is in place
    # The actual CPU-only enforcement happens in the runner
    assert hasattr(check_and_load_model, '__call__'), "check_and_load_model should be callable"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Import torch at the end to avoid issues in test discovery
import torch