import json
import os
import tempfile
import pytest
from pathlib import Path
import sys
import torch

# Add code root to path if running standalone
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.experiments.baseline_runner import BaselineRunner, ExperimentConfig
from src.training.homeostasis import log_gradient_norms
from src.data.benchmarks import generate_training_data, generate_test_data

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

class TestBaselineMetrics:
    """
    Integration test for T015: Verify that run_and_record_metrics
    produces a valid JSON file with the correct schema and logic.
    """

    def test_run_and_record_metrics_creates_file(self, temp_output_dir):
        """
        Test that the baseline runner creates the output file at the specified path.
        """
        output_path = os.path.join(temp_output_dir, "baseline_metrics.json")
        
        # Use a small config for speed in tests
        config = ExperimentConfig(
            hidden_dim=16,
            num_layers=2,
            num_heads=2,
            max_seq_len=32,
            train_epochs=2, # Minimal epochs for unit test speed
            batch_size=16,
            learning_rate=1e-3,
            seed=42,
            device="cpu",
            log_gradients=False
        )
        
        runner = BaselineRunner(config)
        result = runner.run_and_record_metrics(output_path)

        # Assert file exists
        assert os.path.exists(output_path), f"Output file {output_path} was not created"

        # Assert content matches schema
        with open(output_path, 'r') as f:
            data = json.load(f)

        required_keys = {"train_mae", "test_mae", "degradation_pct", "passed"}
        assert required_keys.issubset(data.keys()), f"Missing keys in output: {required_keys - set(data.keys())}"

        # Verify types
        assert isinstance(data["train_mae"], float), "train_mae must be float"
        assert isinstance(data["test_mae"], float), "test_mae must be float"
        assert isinstance(data["degradation_pct"], float), "degradation_pct must be float"
        assert isinstance(data["passed"], bool), "passed must be bool"

    def test_degradation_calculation_logic(self, temp_output_dir):
        """
        Test that degradation_pct is calculated correctly:
        ((test_mae - train_mae) / train_mae) * 100
        """
        # This test is tricky because we can't easily force specific MAE values
        # without mocking the model. Instead, we verify the schema and that
        # the calculation doesn't crash.
        output_path = os.path.join(temp_output_dir, "baseline_metrics.json")
        
        config = ExperimentConfig(
            hidden_dim=16,
            num_layers=2,
            num_heads=2,
            max_seq_len=32,
            train_epochs=1,
            batch_size=16,
            seed=42,
            device="cpu",
            log_gradients=False
        )
        
        runner = BaselineRunner(config)
        result = runner.run_and_record_metrics(output_path)

        # Verify the math logic holds for the returned result
        if result.train_mae > 0:
            expected_deg = ((result.test_mae - result.train_mae) / result.train_mae) * 100
            # Allow small floating point error
            assert abs(result.degradation_pct - expected_deg) < 1e-3, \
                f"Degradation calculation mismatch: {result.degradation_pct} vs {expected_deg}"
        else:
            assert result.degradation_pct == 0.0, "Degradation should be 0 if train_mae is 0"

    def test_passed_flag_logic(self, temp_output_dir):
        """
        Test that 'passed' is True if degradation_pct < 10.0, else False.
        """
        output_path = os.path.join(temp_output_dir, "baseline_metrics.json")
        
        config = ExperimentConfig(
            hidden_dim=16,
            num_layers=2,
            num_heads=2,
            max_seq_len=32,
            train_epochs=1,
            batch_size=16,
            seed=42,
            device="cpu",
            log_gradients=False
        )
        
        runner = BaselineRunner(config)
        result = runner.run_and_record_metrics(output_path)

        if result.degradation_pct < 10.0:
            assert result.passed is True, "passed should be True if degradation < 10%"
        else:
            assert result.passed is False, "passed should be False if degradation >= 10%"

    def test_file_path_matches_task_requirement(self, temp_output_dir):
        """
        Ensure the default output path is data/results/baseline_metrics.json
        """
        # We override the default in the test, but verify the function accepts the path
        custom_path = os.path.join(temp_output_dir, "custom_results.json")
        config = ExperimentConfig(device="cpu", train_epochs=1, seed=42)
        runner = BaselineRunner(config)
        
        # Call with custom path
        runner.run_and_record_metrics(custom_path)
        
        assert os.path.exists(custom_path)
        
        # Verify default path logic (if we called without arg, it would be data/results/...)
        # This is more of a code inspection, but we can verify the default value in the signature
        import inspect
        sig = inspect.signature(BaselineRunner.run_and_record_metrics)
        default_path = sig.parameters['output_path'].default
        assert default_path == "data/results/baseline_metrics.json", \
            f"Default output path is incorrect: {default_path}"