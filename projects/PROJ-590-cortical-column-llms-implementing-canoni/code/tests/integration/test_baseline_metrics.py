import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.experiments.baseline_runner import BaselineRunner, ExperimentConfig

@pytest.fixture
def temp_output_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

class TestBaselineMetrics:
    """
    Integration test for T015: run_and_record_metrics.
    Verifies that the baseline metrics JSON is generated with the correct schema
    and logic (degradation calculation, passed flag).
    """

    def test_run_and_record_metrics_creates_file(self, temp_output_dir):
        """
        Test that run_and_record_metrics successfully creates data/results/baseline_metrics.json.
        """
        config = ExperimentConfig(
            seed=42,
            hidden_dim=16, # Small for speed in test
            num_layers=1,
            num_heads=2,
            max_epochs=2, # Few epochs for test speed
            output_dir=temp_output_dir
        )

        runner = BaselineRunner(config)
        result = runner.run_and_record_metrics()

        # Check file existence
        output_path = os.path.join(temp_output_dir, "baseline_metrics.json")
        assert os.path.exists(output_path), f"Output file {output_path} was not created."

        # Check content
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert "train_mae" in data
        assert "test_mae" in data
        assert "degradation_pct" in data
        assert "passed" in data

        # Check types
        assert isinstance(data["train_mae"], float)
        assert isinstance(data["test_mae"], float)
        assert isinstance(data["degradation_pct"], float)
        assert isinstance(data["passed"], bool)

        # Check result object matches file
        assert data["train_mae"] == result.train_mae
        assert data["test_mae"] == result.test_mae
        assert data["degradation_pct"] == result.degradation_pct
        assert data["passed"] == result.passed

    def test_degradation_logic(self, temp_output_dir):
        """
        Test that degradation_pct is calculated correctly.
        Formula: ((test_mae - train_mae) / train_mae) * 100
        """
        # We rely on the actual run, but we can verify the calculation logic
        # by inspecting the result object directly if we knew the values.
        # Since we don't control the exact values, we verify the formula holds
        # by checking the math in the result object.
        
        config = ExperimentConfig(
            seed=42,
            hidden_dim=16,
            num_layers=1,
            num_heads=2,
            max_epochs=2,
            output_dir=temp_output_dir
        )
        runner = BaselineRunner(config)
        result = runner.run_and_record_metrics()

        # Recalculate expected degradation
        if result.train_mae > 0:
            expected_degradation = ((result.test_mae - result.train_mae) / result.train_mae) * 100
        else:
            expected_degradation = 0.0

        # Allow small floating point tolerance
        assert abs(result.degradation_pct - expected_degradation) < 1e-5, \
            f"Degradation calculation mismatch: {result.degradation_pct} vs {expected_degradation}"

    def test_passed_flag_logic(self, temp_output_dir):
        """
        Test that 'passed' is True if degradation_pct < 10.0, else False.
        """
        config = ExperimentConfig(
            seed=42,
            hidden_dim=16,
            num_layers=1,
            num_heads=2,
            max_epochs=2,
            output_dir=temp_output_dir
        )
        runner = BaselineRunner(config)
        result = runner.run_and_record_metrics()

        expected_passed = result.degradation_pct < 10.0
        assert result.passed == expected_passed, \
            f"Passed flag mismatch: {result.passed} (expected {expected_passed})"