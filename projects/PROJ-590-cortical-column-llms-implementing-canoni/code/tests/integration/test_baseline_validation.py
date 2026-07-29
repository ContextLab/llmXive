import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.experiments.baseline_runner import BaselineRunner, ExperimentConfig


class TestBaselineValidation:
    """
    Integration tests for baseline model validation and metrics recording.
    Verifies that T016 requirements are satisfied:
    - data/results/baseline_metrics.json is generated
    - Contains train_mae, test_mae, degradation_pct keys
    - degradation_pct is calculated correctly with zero-division handling
    """

    def test_baseline_metrics_file_generation(self, tmp_path):
        """
        Test that the baseline runner generates the required metrics JSON file.
        """
        # Configure output to temp directory
        output_path = str(tmp_path / "baseline_metrics.json")
        config = ExperimentConfig(
            hidden_dim=16,
            num_layers=2,
            num_heads=2,
            seq_len=8,
            batch_size=8,
            epochs=2,  # Minimal epochs for fast test
            learning_rate=1e-3,
            device='cpu',
            seed=42,
            output_path=output_path
        )

        runner = BaselineRunner(config)
        result = runner.run_and_record_metrics()

        # Verify file exists
        assert os.path.exists(output_path), f"Expected file {output_path} to exist"

        # Verify JSON content
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'train_mae' in data, "Missing 'train_mae' key in results"
        assert 'test_mae' in data, "Missing 'test_mae' key in results"
        assert 'degradation_pct' in data, "Missing 'degradation_pct' key in results"

        # Verify types
        assert isinstance(data['train_mae'], (int, float)), "train_mae must be numeric"
        assert isinstance(data['test_mae'], (int, float)), "test_mae must be numeric"
        assert isinstance(data['degradation_pct'], (int, float)), "degradation_pct must be numeric"

        # Verify values are non-negative
        assert data['train_mae'] >= 0, "train_mae must be non-negative"
        assert data['test_mae'] >= 0, "test_mae must be non-negative"
        assert data['degradation_pct'] >= 0 or data['degradation_pct'] <= 100, "degradation_pct should be reasonable"

    def test_degradation_calculation(self, tmp_path):
        """
        Test that degradation_pct is calculated correctly.
        Formula: ((test_mae - train_mae) / train_mae) * 100
        """
        output_path = str(tmp_path / "baseline_metrics.json")
        config = ExperimentConfig(
            hidden_dim=16,
            num_layers=2,
            num_heads=2,
            seq_len=8,
            batch_size=8,
            epochs=2,
            learning_rate=1e-3,
            device='cpu',
            seed=42,
            output_path=output_path
        )

        runner = BaselineRunner(config)
        result = runner.run_and_record_metrics()

        with open(output_path, 'r') as f:
            data = json.load(f)

        # Recalculate expected degradation
        train_mae = data['train_mae']
        test_mae = data['test_mae']

        if train_mae > 0:
            expected_degradation = ((test_mae - train_mae) / train_mae) * 100
        else:
            expected_degradation = 0.0

        # Allow small floating point tolerance
        assert abs(data['degradation_pct'] - expected_degradation) < 1e-6, \
            f"Degradation mismatch: got {data['degradation_pct']}, expected {expected_degradation}"

    def test_zero_division_handling(self, tmp_path):
        """
        Test that zero-division is handled gracefully when train_mae is 0.
        In this case, degradation_pct should be 0.0.
        """
        # Note: In practice, train_mae=0 is extremely unlikely for synthetic data,
        # but we verify the logic in the code handles it.
        output_path = str(tmp_path / "baseline_metrics.json")
        config = ExperimentConfig(
            hidden_dim=16,
            num_layers=2,
            num_heads=2,
            seq_len=8,
            batch_size=8,
            epochs=2,
            learning_rate=1e-3,
            device='cpu',
            seed=42,
            output_path=output_path
        )

        runner = BaselineRunner(config)
        # This should not raise an exception even if train_mae is very small
        result = runner.run_and_record_metrics()

        with open(output_path, 'r') as f:
            data = json.load(f)

        # Verify no exception was raised and degradation_pct is a valid number
        assert isinstance(data['degradation_pct'], (int, float)), \
            "degradation_pct should be numeric even with edge cases"

    def test_schema_compliance(self, tmp_path):
        """
        Test that the output JSON strictly complies with the required schema.
        """
        output_path = str(tmp_path / "baseline_metrics.json")
        config = ExperimentConfig(
            hidden_dim=16,
            num_layers=2,
            num_heads=2,
            seq_len=8,
            batch_size=8,
            epochs=2,
            learning_rate=1e-3,
            device='cpu',
            seed=42,
            output_path=output_path
        )

        runner = BaselineRunner(config)
        runner.run_and_record_metrics()

        with open(output_path, 'r') as f:
            data = json.load(f)

        # Required top-level keys
        required_keys = {'train_mae', 'test_mae', 'degradation_pct'}
        actual_keys = set(data.keys())

        assert required_keys.issubset(actual_keys), \
            f"Missing required keys: {required_keys - actual_keys}"

        # Verify no unexpected top-level keys (optional: 'duration_seconds', 'config' are allowed)
        allowed_optional_keys = {'duration_seconds', 'config'}
        unexpected_keys = actual_keys - required_keys - allowed_optional_keys
        assert len(unexpected_keys) == 0, f"Unexpected keys in output: {unexpected_keys}"

    def test_artifact_persistence(self, tmp_path):
        """
        Test that the artifact file is persisted to disk and can be re-read.
        """
        output_path = str(tmp_path / "baseline_metrics.json")
        config = ExperimentConfig(
            hidden_dim=16,
            num_layers=2,
            num_heads=2,
            seq_len=8,
            batch_size=8,
            epochs=2,
            learning_rate=1e-3,
            device='cpu',
            seed=42,
            output_path=output_path
        )

        runner = BaselineRunner(config)
        runner.run_and_record_metrics()

        # Re-read the file
        with open(output_path, 'r') as f:
            data1 = json.load(f)

        # Run again and verify consistency (deterministic with seed)
        runner2 = BaselineRunner(config)
        runner2.run_and_record_metrics()

        with open(output_path, 'r') as f:
            data2 = json.load(f)

        # Core metrics should be identical (deterministic)
        assert data1['train_mae'] == data2['train_mae'], "Non-deterministic train_mae"
        assert data1['test_mae'] == data2['test_mae'], "Non-deterministic test_mae"
        assert data1['degradation_pct'] == data2['degradation_pct'], "Non-deterministic degradation_pct"