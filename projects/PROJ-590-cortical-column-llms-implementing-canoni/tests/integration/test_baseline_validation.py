"""
Integration test for baseline model validation and degradation measurement.

This test verifies that the baseline training pipeline correctly records
Mean Absolute Error (MAE) on both training and independent test sets,
calculates the degradation percentage, and stores these metrics in
data/results/baseline_metrics.json for downstream cost curve generation.

No hard pass/fail threshold is enforced on degradation; the test asserts
that the metrics are recorded and the JSON file is created with the
expected schema.
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest
import torch

# Add project root to path if running outside pytest environment
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.benchmarks import generate_synthetic_dataset
from src.models.baseline_transformer import BaselineTransformer
from src.training.trainer import TrainingConfig, run_training, calculate_mae
from src.experiments.baseline_runner import BaselineRunner, ExperimentConfig


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    # Cleanup after test
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)


@pytest.fixture
def synthetic_data():
    """Generate deterministic synthetic datasets for testing."""
    # Training data: Lorenz attractor
    train_data = generate_synthetic_dataset(
        task_type="lorenz",
        n_samples=500,
        seed=42,
        noise_level=0.01
    )

    # Test data: Independent Lorenz attractor (different seed)
    test_data = generate_synthetic_dataset(
        task_type="lorenz",
        n_samples=200,
        seed=123,  # Different seed for independence
        noise_level=0.01
    )

    return train_data, test_data


def test_baseline_degradation_measurement(synthetic_data, temp_output_dir):
    """
    Test that baseline model training records MAE on both training and test sets,
    calculates degradation percentage, and stores metrics in JSON format.

    This test asserts:
    1. The baseline_runner produces valid training and test MAE values
    2. The degradation percentage is calculated correctly
    3. The metrics are stored in data/results/baseline_metrics.json
    4. The JSON schema matches the expected structure
    """
    train_data, test_data = synthetic_data

    # Ensure output directory exists
    results_dir = Path(temp_output_dir) / "data" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_file = results_dir / "baseline_metrics.json"

    # Create experiment configuration
    # Note: Using small hidden dimensions and layers for CPU test speed
    config = ExperimentConfig(
        task_type="lorenz",
        hidden_dim=16,
        num_layers=2,
        num_heads=2,
        dropout=0.1,
        learning_rate=0.001,
        batch_size=32,
        epochs=5,
        seed=42,
        output_dir=temp_output_dir
    )

    # Create runner and execute training
    runner = BaselineRunner(config)

    # Train model on training data
    train_mae, test_mae = runner.train_and_evaluate(
        train_data=train_data,
        test_data=test_data
    )

    # Verify that MAE values are computed and are finite
    assert isinstance(train_mae, float), "Training MAE must be a float"
    assert isinstance(test_mae, float), "Test MAE must be a float"
    assert not torch.isnan(torch.tensor(train_mae)), "Training MAE must be finite"
    assert not torch.isnan(torch.tensor(test_mae)), "Test MAE must be finite"
    assert train_mae >= 0, "Training MAE must be non-negative"
    assert test_mae >= 0, "Test MAE must be non-negative"

    # Calculate degradation percentage
    # Degradation = (Test MAE - Train MAE) / Train MAE * 100
    if train_mae > 0:
        degradation_pct = ((test_mae - train_mae) / train_mae) * 100
    else:
        # Avoid division by zero
        degradation_pct = float('inf') if test_mae > 0 else 0.0

    # Verify output file exists
    assert output_file.exists(), f"Output file {output_file} was not created"

    # Load and validate JSON structure
    with open(output_file, 'r') as f:
        metrics = json.load(f)

    # Assert expected schema
    expected_keys = {
        'task_type',
        'train_mae',
        'test_mae',
        'degradation_pct',
        'config',
        'timestamp'
    }

    actual_keys = set(metrics.keys())
    assert expected_keys.issubset(actual_keys), (
        f"Missing keys in metrics JSON. Expected: {expected_keys}, Got: {actual_keys}"
    )

    # Verify metric values match computed values
    assert abs(metrics['train_mae'] - train_mae) < 1e-6, "Train MAE mismatch"
    assert abs(metrics['test_mae'] - test_mae) < 1e-6, "Test MAE mismatch"
    assert abs(metrics['degradation_pct'] - degradation_pct) < 1e-4, (
        f"Degradation percentage mismatch. Expected: {degradation_pct}, Got: {metrics['degradation_pct']}"
    )

    # Verify task type is recorded
    assert metrics['task_type'] == 'lorenz', "Task type mismatch"

    # Verify config is stored
    assert 'hidden_dim' in metrics['config'], "Config must include hidden_dim"
    assert metrics['config']['hidden_dim'] == config.hidden_dim, "Config mismatch"

    # Verify timestamp exists and is a string
    assert isinstance(metrics['timestamp'], str), "Timestamp must be a string"
    assert len(metrics['timestamp']) > 0, "Timestamp must not be empty"

    # The test passes as long as metrics are recorded correctly.
    # No hard threshold on degradation percentage is enforced per task requirements.
    # Degradation can be negative (test performs better than train) or positive.
    # We only assert that the calculation was performed and stored.