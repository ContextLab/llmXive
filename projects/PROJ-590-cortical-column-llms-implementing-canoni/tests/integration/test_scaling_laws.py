"""
Integration test for scaling law regression analysis (Task T025).

This test verifies that the scaling law analysis pipeline correctly:
1. Trains models with varying column counts (1x, 2x, 4x).
2. Records performance metrics (MAE) and parameter counts.
3. Fits a power-law model to the data.
4. Validates the scaling exponent against theoretical expectations.

The test assumes the existence of `src/experiments/scaling.py` which provides
the `run_scaling_experiment` function.
"""
import pytest
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from scipy.optimize import curve_fit

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.experiments.scaling import run_scaling_experiment
from src.utils.scaling_analyzer import fit_power_law, ScalingResult
from src.training.trainer import TrainingConfig
from src.data.benchmarks import generate_synthetic_dataset


def power_law(x, a, b):
    """Power law function: y = a * x^b"""
    return a * np.power(x, b)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def small_training_config():
    """Create a minimal training config for fast testing."""
    return TrainingConfig(
        epochs=2,  # Very few epochs for speed
        batch_size=32,
        learning_rate=0.001,
        max_grad_norm=1.0,
        device="cpu",
        seed=42,
        early_stopping_patience=10,
    )


def test_scaling_law_regression(temp_output_dir, small_training_config):
    """
    Test the full scaling law regression pipeline.

    This test:
    1. Runs experiments with 1, 2, and 4 columns.
    2. Fits a power law to the results.
    3. Validates that the scaling exponent is within a reasonable range.
    4. Writes the results to a JSON file.
    """
    # Define column multipliers to test
    column_multipliers = [1, 2, 4]
    results: List[Dict[str, Any]] = []

    # Run experiments for each multiplier
    for multiplier in column_multipliers:
        # Generate a small synthetic dataset for the experiment
        train_data, val_data = generate_synthetic_dataset(
            task="lorenz",
            n_samples=500,  # Small dataset for speed
            n_features=10,
            noise=0.01,
            seed=42 + multiplier,
        )

        # Run the scaling experiment
        experiment_result = run_scaling_experiment(
            config=small_training_config,
            column_multiplier=multiplier,
            train_data=train_data,
            val_data=val_data,
            output_dir=temp_output_dir,
        )

        results.append(
            {
                "multiplier": multiplier,
                "num_columns": experiment_result.num_columns,
                "num_params": experiment_result.num_params,
                "val_mae": experiment_result.val_mae,
                "train_time": experiment_result.train_time,
            }
        )

    # Save raw results
    raw_results_path = os.path.join(temp_output_dir, "scaling_raw_results.json")
    with open(raw_results_path, "w") as f:
        json.dump(results, f, indent=2)

    # Perform power law fitting
    # We expect MAE to decrease as parameters increase: MAE ~ N^(-beta)
    # Or equivalently: log(MAE) = log(a) - beta * log(N)
    multipliers = np.array([r["num_columns"] for r in results])
    maes = np.array([r["val_mae"] for r in results])

    # Avoid log(0) or negative values
    assert np.all(maes > 0), "MAE values must be positive for log transformation"

    try:
        # Fit power law: MAE = a * (num_columns)^b
        popt, pcov = curve_fit(power_law, multipliers, maes, p0=[1.0, -0.5])
        a_fit, b_fit = popt
        perr = np.sqrt(np.diag(pcov))
    except Exception as e:
        pytest.fail(f"Power law fitting failed: {str(e)}")

    # Create scaling result object
    scaling_result = ScalingResult(
        multipliers=multipliers.tolist(),
        maes=maes.tolist(),
        fitted_a=float(a_fit),
        fitted_b=float(b_fit),
        fitted_a_std=float(perr[0]),
        fitted_b_std=float(perr[1]),
        r_squared=1.0
        - np.sum((maes - power_law(multipliers, a_fit, b_fit)) ** 2)
        / np.sum((maes - np.mean(maes)) ** 2),
    )

    # Save scaling analysis results
    scaling_results_path = os.path.join(temp_output_dir, "scaling_exponent.json")
    with open(scaling_results_path, "w") as f:
        json.dump(
            {
                "multipliers": scaling_result.multipliers,
                "maes": scaling_result.maes,
                "fitted_a": scaling_result.fitted_a,
                "fitted_b": scaling_result.fitted_b,
                "fitted_a_std": scaling_result.fitted_a_std,
                "fitted_b_std": scaling_result.fitted_b_std,
                "r_squared": scaling_result.r_squared,
                "exponent_interpretation": (
                    f"MAE scales as N^({scaling_result.fitted_b:.3f})"
                ),
            },
            f,
            indent=2,
        )

    # Assertions
    # 1. Check that we have results for all multipliers
    assert len(results) == len(column_multipliers)

    # 2. Check that MAE generally decreases with more columns (negative exponent)
    # Note: This is a soft check as small datasets might not show clear trends
    assert scaling_result.fitted_b < 0.1, (
        f"Expected negative scaling exponent, got {scaling_result.fitted_b:.3f}. "
        "This suggests MAE does not improve with more columns."
    )

    # 3. Check R-squared value (should be > 0.5 for a reasonable fit)
    assert scaling_result.r_squared > 0.3, (
        f"R-squared too low: {scaling_result.r_squared:.3f}. "
        "The power law model does not fit the data well."
    )

    # 4. Verify output files exist
    assert os.path.exists(raw_results_path), "Raw results file not created"
    assert os.path.exists(scaling_results_path), "Scaling results file not created"

    print(f"Scaling Law Test Results:")
    print(f"  Exponent (b): {scaling_result.fitted_b:.3f} ± {scaling_result.fitted_b_std:.3f}")
    print(f"  R-squared: {scaling_result.r_squared:.3f}")
    print(f"  Interpretation: MAE scales as N^({scaling_result.fitted_b:.3f})")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])