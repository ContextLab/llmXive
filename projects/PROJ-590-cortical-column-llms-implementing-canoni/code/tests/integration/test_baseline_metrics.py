import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.experiments.baseline_runner import BaselineRunner, ExperimentConfig

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

class TestBaselineMetrics:
    """Integration tests for baseline metrics generation (T015)."""

    def test_run_and_record_metrics_creates_file(self, temp_output_dir):
        """Test that run_and_record_metrics writes the correct JSON file."""
        output_path = os.path.join(temp_output_dir, "baseline_metrics.json")

        # Use a small config for faster testing
        config = ExperimentConfig(
            name="test_baseline",
            hidden_dim=16,
            num_layers=2,
            num_heads=2,
            seq_len=32,
            train_samples=100,
            test_samples=50,
            epochs=2,
            batch_size=16,
            lr=1e-3,
            seed=42,
        )

        runner = BaselineRunner(config)
        result = runner.run_and_record_metrics(output_path=output_path)

        # Verify file exists
        assert os.path.exists(output_path), f"Output file {output_path} was not created"

        # Verify JSON schema
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert "train_mae" in data
        assert "test_mae" in data
        assert "degradation_pct" in data
        assert "passed" in data

        # Verify types
        assert isinstance(data["train_mae"], float)
        assert isinstance(data["test_mae"], float)
        assert isinstance(data["degradation_pct"], float)
        assert isinstance(data["passed"], bool)

        # Verify precision (4 decimal places)
        assert len(str(data["train_mae"]).split('.')[-1]) <= 4
        assert len(str(data["test_mae"]).split('.')[-1]) <= 4

        # Verify logic for 'passed'
        if data["degradation_pct"] < 10.0:
            assert data["passed"] is True
        else:
            assert data["passed"] is False

    def test_run_and_record_metrics_returns_result(self, temp_output_dir):
        """Test that run_and_record_metrics returns a valid ExperimentResult."""
        output_path = os.path.join(temp_output_dir, "baseline_metrics.json")

        config = ExperimentConfig(
            name="test_baseline",
            hidden_dim=16,
            num_layers=2,
            num_heads=2,
            seq_len=32,
            train_samples=100,
            test_samples=50,
            epochs=2,
            batch_size=16,
            lr=1e-3,
            seed=42,
        )

        runner = BaselineRunner(config)
        result = runner.run_and_record_metrics(output_path=output_path)

        assert result.train_mae == pytest.approx(json.load(open(output_path))["train_mae"], rel=1e-4)
        assert result.test_mae == pytest.approx(json.load(open(output_path))["test_mae"], rel=1e-4)
        assert result.degradation_pct == pytest.approx(json.load(open(output_path))["degradation_pct"], rel=1e-4)
        assert result.passed == json.load(open(output_path))["passed"]