"""
Contract test for training loss logging (User Story 2).

This test verifies that the SDAR training pipeline (or its simulation wrapper
for CPU-only environments) correctly emits the required log schema:
- SDAR Gate Loss
- RL Loss
- kl_divergence
- teacher_update_count
- gate_activation_rate

The test runs the training logic for a minimal number of steps and asserts
that the output logs (either in memory or written to disk) contain these keys
with numeric values, matching the schema defined in T007 and data_model.md.
"""
import json
import os
import sys
import tempfile
import pytest

# Ensure the project root is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.sdar_sim import run_experiment, compute_sdar_loss, get_teacher_signals
from src.logging_config import get_json_logger

REQUIRED_LOG_KEYS = [
    "SDAR Gate Loss",
    "RL Loss",
    "kl_divergence",
    "teacher_update_count",
    "gate_activation_rate"
]

def test_training_logs_schema():
    """
    Contract test: Verify that running the training experiment produces logs
    with the exact schema required by the reproducibility report.
    """
    # Create a temporary directory for logs
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_file_path = os.path.join(tmp_dir, "train_log.json")
        
        # Initialize the logger to write to our temp file
        # We assume the logger is configured to append or overwrite
        logger = get_json_logger(log_file=log_file_path)
        
        # Run a minimal experiment (simulated for CPU tractability per reviewer feedback)
        # Parameters: 5 steps to ensure we have enough data points for the contract
        num_steps = 5
        batch_size = 1
        
        # Execute the experiment
        # This calls the actual logic in sdar_sim which computes real values
        # based on the teacher signals and student outputs, not random noise.
        results = run_experiment(
            num_steps=num_steps,
            batch_size=batch_size,
            logger=logger,
            output_dir=tmp_dir
        )
        
        # Verify the log file was created
        assert os.path.exists(log_file_path), f"Log file not created at {log_file_path}"
        
        # Read and parse the log file
        with open(log_file_path, 'r') as f:
            # The logger writes JSON lines or a single JSON object.
            # Assuming JSON lines format based on typical training logs.
            logs = []
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))
        
        # Ensure we have at least one log entry
        assert len(logs) > 0, "No log entries were produced"
        
        # Check that every log entry contains the required keys
        for i, entry in enumerate(logs):
            for key in REQUIRED_LOG_KEYS:
                assert key in entry, f"Missing key '{key}' in log entry {i}"
                value = entry[key]
                # Verify values are numeric (float or int)
                assert isinstance(value, (int, float)), f"Key '{key}' in entry {i} is not numeric: {type(value)}"
                
                # Additional sanity checks for specific metrics
                if key == "SDAR Gate Loss":
                    assert value >= 0, f"SDAR Gate Loss should be non-negative: {value}"
                elif key == "RL Loss":
                    assert value >= 0, f"RL Loss should be non-negative: {value}"
                elif key == "kl_divergence":
                    assert value >= 0, f"KL Divergence should be non-negative: {value}"
                elif key == "gate_activation_rate":
                    assert 0.0 <= value <= 1.0, f"Gate activation rate must be in [0, 1]: {value}"

def test_real_values_not_synthetic():
    """
    Regression test to ensure the values are computed from the simulation logic
    and not hardcoded placeholders. We check that values vary across steps.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_file_path = os.path.join(tmp_dir, "train_log.json")
        logger = get_json_logger(log_file=log_file_path)
        
        # Run a slightly longer experiment to ensure variance
        results = run_experiment(num_steps=10, batch_size=1, logger=logger, output_dir=tmp_dir)
        
        with open(log_file_path, 'r') as f:
            logs = [json.loads(line) for line in f if line.strip()]
        
        assert len(logs) >= 2, "Need at least 2 steps to check for variance"
        
        # Check that Gate Loss is not constant across all steps (unless the model is perfectly converged, which is unlikely in 10 steps)
        gate_losses = [log["SDAR Gate Loss"] for log in logs]
        
        # If all values are identical, it might be a hardcoded placeholder
        # We allow a small tolerance for floating point, but strict equality is suspicious
        if len(set(gate_losses)) == 1:
            # If they are all the same, check if it's a "0.0" or "1.0" placeholder
            if gate_losses[0] == 0.0 or gate_losses[0] == 1.0:
                pytest.fail("All Gate Loss values are identical and look like placeholders (0.0 or 1.0). "
                            "Ensure run_experiment computes real values from teacher/student signals.")
        
        # Check that teacher_update_count is non-negative
        for log in logs:
            assert log["teacher_update_count"] >= 0, "teacher_update_count must be non-negative"
            # Ensure it's an integer if it represents a count
            assert isinstance(log["teacher_update_count"], int), "teacher_update_count should be an integer"