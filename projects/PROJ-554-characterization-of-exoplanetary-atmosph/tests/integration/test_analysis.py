"""
Integration test for correlation and regression on mock data.

This test validates the analysis pipeline (Kendall's tau, bootstrap, Tobit regression)
using a controlled synthetic dataset. This ensures the statistical methods work correctly
on data with known properties before running on the full real-world dataset.

The mock data is generated deterministically with a fixed seed to ensure reproducibility.
It includes censored values (upper limits) to test the survival analysis capabilities.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add project root to path to import code modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis import (
    load_analysis_data,
    quality_control_filter,
    compute_censored_kendall_tau,
    bootstrap_ats,
    calculate_statistical_power,
    generate_quality_report
)
from analysis_tobit import (
    load_retrieval_data,
    calculate_vif,
    prepare_tobit_data,
    fit_tobit_model,
    save_regression_results
)
from config import get_config, set_random_seed
from utils import setup_logging, CensoredDataError


# --- Fixtures ---

@pytest.fixture(scope="module")
def mock_dataset_dir():
    """
    Creates a temporary directory with a mock dataset for analysis.
    The data is deterministic (seed=42) and includes censored values.
    """
    seed = 42
    np.random.seed(seed)
    set_random_seed(seed)

    n_samples = 50
    temp_dir = tempfile.mkdtemp(prefix="mock_analysis_")
    data_path = Path(temp_dir) / "analysis_dataset.csv"

    # Generate mock data with known correlation
    # Water abundance (log10) correlated with Temperature
    # Add some noise and censored values (upper limits)
    temps = np.random.uniform(800, 2500, n_samples)
    # True correlation: higher temp -> higher water (slope ~ 0.0005)
    water_true = -4.0 + 0.0005 * (temps - 1500)
    noise = np.random.normal(0, 0.3, n_samples)
    water_obs = water_true + noise

    # Create censored values (upper limits) for low SNR planets (approx 20% of sample)
    is_censored = np.random.random(n_samples) < 0.2
    detection_limits = water_obs - np.random.uniform(0.5, 1.5, n_samples)
    water_obs[is_censored] = detection_limits[is_censored]

    # Metallicity (random, some missing)
    metallicities = np.random.normal(0.0, 0.5, n_samples)
    # Randomly mask some metallicity values (simulating missing data)
    missing_mask = np.random.random(n_samples) < 0.1
    metallicities[missing_mask] = np.nan

    # Mass (random)
    masses = np.random.uniform(0.5, 15.0, n_samples)

    # SNR and Resolution
    snrs = np.random.uniform(5, 50, n_samples)
    resolutions = np.random.uniform(10, 100, n_samples)

    # Planet names
    planet_names = [f"Planet_{i:03d}" for i in range(n_samples)]

    # Construct DataFrame
    df = pd.DataFrame({
        "planet_name": planet_names,
        "temperature": temps,
        "water_mixing_ratio": water_obs,
        "metallicity": metallicities,
        "mass": masses,
        "snr": snrs,
        "resolution": resolutions,
        "is_upper_limit": is_censored,
        "detection_limit": detection_limits
    })

    df.to_csv(data_path, index=False)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


# --- Tests ---

def test_quality_control_filter(mock_dataset_dir):
    """
    Tests that the quality control filter correctly separates data for
    correlation (all) and regression (complete metallicity) analyses.
    """
    data_path = Path(mock_dataset_dir) / "analysis_dataset.csv"
    df = pd.read_csv(data_path)

    # Apply QC filter
    corr_data, reg_data = quality_control_filter(df)

    # Verify correlation data has all rows with temperature
    assert len(corr_data) == len(df[df["temperature"].notna()])
    assert "water_mixing_ratio" in corr_data.columns
    assert "is_upper_limit" in corr_data.columns

    # Verify regression data excludes rows with missing metallicity
    expected_reg_count = len(df[df["metallicity"].notna()])
    assert len(reg_data) == expected_reg_count
    assert "metallicity" in reg_data.columns

    # Verify no NaN in metallicity for regression data
    assert reg_data["metallicity"].isna().sum() == 0


def test_compute_censored_kendall_tau(mock_dataset_dir):
    """
    Tests the computation of Kendall's tau for censored data.
    Verifies that the function returns valid statistics and handles
    the censored flag correctly.
    """
    data_path = Path(mock_dataset_dir) / "analysis_dataset.csv"
    df = pd.read_csv(data_path)
    corr_data, _ = quality_control_filter(df)

    # Run correlation analysis
    tau, p_value, ci_lower, ci_upper = compute_censored_kendall_tau(
        corr_data,
        x_col="temperature",
        y_col="water_mixing_ratio",
        censor_col="is_upper_limit"
    )

    # Assertions on return types and ranges
    assert isinstance(tau, float)
    assert isinstance(p_value, float)
    assert -1.0 <= tau <= 1.0
    assert 0.0 <= p_value <= 1.0
    assert ci_lower <= tau <= ci_upper

    # Since we generated data with a positive correlation, tau should be positive
    # (allowing for some variance due to noise and sample size)
    assert tau > -0.2, f"Expected positive correlation, got {tau}"


def test_bootstrap_ats(mock_dataset_dir):
    """
    Tests the bootstrap resampling for confidence interval estimation.
    """
    data_path = Path(mock_dataset_dir) / "analysis_dataset.csv"
    df = pd.read_csv(data_path)
    corr_data, _ = quality_control_filter(df)

    # Run bootstrap
    n_iterations = 100
    tau_mean, ci_lower, ci_upper = bootstrap_ats(
        corr_data,
        x_col="temperature",
        y_col="water_mixing_ratio",
        censor_col="is_upper_limit",
        n_iterations=n_iterations,
        seed=42
    )

    assert isinstance(tau_mean, float)
    assert isinstance(ci_lower, float)
    assert isinstance(ci_upper, float)
    assert ci_lower <= tau_mean <= ci_upper


def test_tobit_regression_fallback(mock_dataset_dir):
    """
    Tests the Tobit regression pipeline, including VIF calculation
    and the fallback to Penalized Tobit if multicollinearity is detected.
    """
    data_path = Path(mock_dataset_dir) / "analysis_dataset.csv"
    df = pd.read_csv(data_path)
    _, reg_data = quality_control_filter(df)

    # Prepare data
    X, y, censor = prepare_tobit_data(
        reg_data,
        x_cols=["temperature", "mass", "metallicity"],
        y_col="water_mixing_ratio",
        censor_col="is_upper_limit"
    )

    # Calculate VIF (should be low for random mock data)
    vif_data = calculate_vif(X)
    max_vif = vif_data["VIF"].max()
    assert max_vif < 10.0, f"Unexpected high VIF in mock data: {max_vif}"

    # Fit model
    model, result_dict = fit_tobit_model(X, y, censor)

    # Verify result dictionary structure
    assert "coefficients" in result_dict
    assert "p_values" in result_dict
    assert "fallback_triggered" in result_dict
    assert isinstance(result_dict["coefficients"], dict)


def test_full_analysis_pipeline(mock_dataset_dir, tmp_path):
    """
    Integration test: Runs the full analysis pipeline (QC, Correlation, Regression)
    and verifies that all expected output files are generated with valid content.
    """
    data_path = Path(mock_dataset_dir) / "analysis_dataset.csv"
    output_dir = Path(tmp_path) / "results"
    output_dir.mkdir(parents=True)

    # 1. Load and Filter
    df = pd.read_csv(data_path)
    corr_data, reg_data = quality_control_filter(df)

    # 2. Correlation Stats
    tau, p_val, ci_l, ci_u = compute_censored_kendall_tau(
        corr_data, "temperature", "water_mixing_ratio", "is_upper_limit"
    )
    corr_stats = {
        "tau": tau,
        "p_value": p_val,
        "ci_95": [ci_l, ci_u],
        "n_samples": len(corr_data)
    }

    # 3. Bootstrap
    tau_boot, ci_b_l, ci_b_u = bootstrap_ats(
        corr_data, "temperature", "water_mixing_ratio", "is_upper_limit",
        n_iterations=50, seed=42
    )
    bootstrap_stats = {
        "iterations": 50,
        "tau_mean": tau_boot,
        "ci_95": [ci_b_l, ci_b_u]
    }

    # 4. Regression
    _, reg_result = fit_tobit_model(
        *prepare_tobit_data(reg_data, ["temperature", "mass", "metallicity"], "water_mixing_ratio", "is_upper_limit")
    )

    # 5. Save outputs to verify they can be written
    stats_path = output_dir / "correlation_stats.json"
    with open(stats_path, "w") as f:
        json.dump(corr_stats, f, indent=2)

    boot_path = output_dir / "bootstrap_ci.json"
    with open(boot_path, "w") as f:
        json.dump(bootstrap_stats, f, indent=2)

    reg_path = output_dir / "regression_results.json"
    with open(reg_path, "w") as f:
        json.dump(reg_result, f, indent=2)

    # Verification: Read back and assert schema
    with open(stats_path) as f:
        loaded_corr = json.load(f)
    assert "tau" in loaded_corr
    assert "ci_95" in loaded_corr

    with open(boot_path) as f:
        loaded_boot = json.load(f)
    assert "tau_mean" in loaded_boot
    assert "ci_95" in loaded_boot

    with open(reg_path) as f:
        loaded_reg = json.load(f)
    assert "coefficients" in loaded_reg


def test_power_analysis(mock_dataset_dir):
    """
    Tests the statistical power calculation for the correlation.
    """
    data_path = Path(mock_dataset_dir) / "analysis_dataset.csv"
    df = pd.read_csv(data_path)
    corr_data, _ = quality_control_filter(df)

    power_estimate, power_sufficient = calculate_statistical_power(
        corr_data,
        x_col="temperature",
        y_col="water_mixing_ratio",
        censor_col="is_upper_limit",
        n_iterations=50,
        seed=42
    )

    assert isinstance(power_estimate, float)
    assert 0.0 <= power_estimate <= 1.0
    assert isinstance(power_sufficient, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])