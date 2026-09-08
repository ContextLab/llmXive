"""
Unit tests for T021c: Threshold Identification.
"""
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest

# Import the function to test
# We need to import from the analysis module
# Assuming the project root is in the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.threshold_identification import (
    load_validated_sweep_results,
    fit_logistic_model,
    validate_residuals,
    estimate_theta_c,
    calculate_confidence_interval,
    run_threshold_identification
)


def create_dummy_csv(filepath: Path, thetas: list, flags: list):
    """Helper to create a dummy CSV file."""
    with open(filepath, 'w') as f:
        f.write("theta,outlier_flag\n")
        for t, f in zip(thetas, flags):
            f.write(f"{t},{f}\n")


def test_load_validated_sweep_results():
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test.csv"
        thetas = [1.0, 2.0, 3.0]
        flags = [0, 1, 1]
        create_dummy_csv(csv_path, thetas, flags)

        loaded_thetas, loaded_flags = load_validated_sweep_results(csv_path)

        np.testing.assert_array_almost_equal(loaded_thetas, thetas)
        np.testing.assert_array_almost_equal(loaded_flags, flags)


def test_fit_logistic_model():
    # Create a simple dataset where the transition is clear
    thetas = np.array([1.0, 1.5, 2.0, 2.5, 3.0])
    # Hard-coded transition at 2.0
    flags = np.array([0, 0, 0, 1, 1])

    model, probs, loss = fit_logistic_model(thetas, flags)

    assert model is not None
    assert len(probs) == len(thetas)
    assert loss >= 0.0


def test_validate_residuals():
    # Perfect fit
    y_true = np.array([0.0, 1.0])
    y_pred = np.array([0.0, 1.0])
    is_valid, max_res = validate_residuals(y_true, y_pred)
    assert is_valid
    assert max_res == 0.0

    # Imperfect fit
    y_pred_bad = np.array([0.1, 0.9])
    is_valid_bad, max_res_bad = validate_residuals(y_true, y_pred_bad)
    assert not is_valid_bad
    assert max_res_bad > 0.0


def test_estimate_theta_c():
    # Create a model with known coefficients
    # P(y=1) = sigmoid(10 * (x - 2.0))
    # So w = 10, b = -20.0
    # theta_c = -b/w = 2.0
    from sklearn.linear_model import LogisticRegression
    model = LogisticRegression(solver='lbfgs', max_iter=1000)
    # We can't easily set coefficients directly, so we'll fit a perfect dataset
    thetas = np.array([1.0, 1.5, 2.0, 2.5, 3.0])
    flags = np.array([0, 0, 0, 1, 1])
    model.fit(thetas.reshape(-1, 1), flags)

    theta_c = estimate_theta_c(model)
    # The estimated theta_c should be close to 2.0
    assert 1.5 < theta_c < 2.5


def test_run_threshold_identification():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.json"

        # Create data with a clear transition
        thetas = [1.0, 1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.4, 2.6, 2.8, 3.0]
        # Add some noise
        flags = [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1]

        create_dummy_csv(input_path, thetas, flags)

        result = run_threshold_identification(input_path, output_path)

        assert "critical_threshold" in result
        assert "theta_c" in result["critical_threshold"]
        assert "confidence_interval_95" in result["critical_threshold"]
        assert "validation" in result
        assert "is_valid" in result["validation"]

        # Check that output file exists
        assert output_path.exists()

        with open(output_path, 'r') as f:
            saved_result = json.load(f)
            assert saved_result == result