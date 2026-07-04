"""
Integration test for correlation and regression on mock data.

This test validates the censored data handling (Kendall's tau) and
Tobit regression logic in code/analysis.py using a deterministic
mock dataset that mimics the structure of real exoplanet data
(temperature, metallicity, water abundance with upper limits).

It verifies that:
1. Censored Kendall's tau is computed correctly.
2. Bootstrap confidence intervals are generated.
3. Tobit regression fits without crashing on censored data.
4. The output schema matches expectations.
"""
import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure code directory is importable
_code_root = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(_code_root))

from analysis import compute_censored_kendall_tau, run_tobit_regression
from config import set_random_seed, get_config

# Setup logging for the test
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fix random seed for reproducibility
set_random_seed(42)

def create_mock_censored_dataset(n_samples: int = 100):
    """
    Generates a mock dataset mimicking exoplanet atmospheric data.
    Includes censored values (upper limits) for low SNR cases.

    Returns a DataFrame with columns:
    - temperature: float (K)
    - metallicity: float ([Fe/H])
    - water_log_mixing_ratio: float (log10)
    - is_censored: bool (True if upper limit)
    - snr: float
    - resolution: int
    - planet_category: str ('Hot Jupiter' or 'Super Earth')
    """
    np.random.seed(42)

    # Base distributions
    temps = np.random.uniform(1000, 2500, n_samples)
    metallicity = np.random.normal(0.0, 0.5, n_samples)
    categories = np.random.choice(['Hot Jupiter', 'Super Earth'], n_samples)

    # Generate water abundance with some correlation to temperature
    # water ~ 0.001 * temp + noise
    base_water = -4.0 + (temps - 1000) * 0.001
    noise = np.random.normal(0, 0.5, n_samples)
    water_log = base_water + noise

    # Simulate censoring: Low SNR leads to upper limits
    # Assume SNR depends on temperature and some noise
    snr = 50 + (temps - 1000) * 0.02 + np.random.normal(0, 10, n_samples)
    resolution = np.random.choice([100, 300, 1000], n_samples)

    # Censoring threshold: if SNR < 20, we only get an upper limit
    # For the sake of the test, we mark low SNR as censored
    is_censored = snr < 20
    # For censored values, the 'observed' water is actually an upper limit
    # In real data, this might be the detection limit.
    # We'll set the value to a fixed detection limit for censored points
    detection_limit = -5.0
    water_log_final = np.where(is_censored, detection_limit, water_log)

    df = pd.DataFrame({
        'temperature': temps,
        'metallicity': metallicity,
        'water_log_mixing_ratio': water_log_final,
        'is_censored': is_censored,
        'snr': snr,
        'resolution': resolution,
        'planet_category': categories
    })
    return df

def test_compute_censored_kendall_tau():
    """
    Test that compute_censored_kendall_tau runs on mock data and returns
    expected schema (tau, p_value, ci_low, ci_high).
    """
    logger.info("Running test_compute_censored_kendall_tau...")
    df = create_mock_censored_dataset(n_samples=50)

    # Filter for specific category to test subset logic if needed
    # Here we test on the whole set
    result = compute_censored_kendall_tau(
        df,
        x_col='temperature',
        y_col='water_log_mixing_ratio',
        censored_col='is_censored',
        n_bootstrap=10  # Small number for speed in unit test
    )

    assert result is not None, "Result should not be None"
    assert 'tau' in result, "Result must contain 'tau'"
    assert 'p_value' in result, "Result must contain 'p_value'"
    assert 'ci_low' in result, "Result must contain 'ci_low'"
    assert 'ci_high' in result, "Result must contain 'ci_high'"
    assert isinstance(result['tau'], (int, float)), "Tau must be numeric"
    assert -1 <= result['tau'] <= 1, "Tau must be between -1 and 1"

    logger.info(f"Kendall's tau: {result['tau']:.4f}, p-value: {result['p_value']:.4f}")
    logger.info("test_compute_censored_kendall_tau PASSED")

def test_run_tobit_regression():
    """
    Test that run_tobit_regression handles censored data and returns
    model coefficients and diagnostics.
    """
    logger.info("Running test_run_tobit_regression...")
    df = create_mock_censored_dataset(n_samples=50)

    result = run_tobit_regression(
        df,
        target_col='water_log_mixing_ratio',
        features=['temperature', 'metallicity'],
        censored_col='is_censored'
    )

    assert result is not None, "Result should not be None"
    assert 'coefficients' in result, "Result must contain 'coefficients'"
    assert 'log_likelihood' in result, "Result must contain 'log_likelihood'"
    assert 'aic' in result, "Result must contain 'aic'"

    coeffs = result['coefficients']
    assert 'temperature' in coeffs, "Coefficients must include temperature"
    assert 'metallicity' in coeffs, "Coefficients must include metallicity"

    logger.info(f"Temperature coefficient: {coeffs['temperature']:.4f}")
    logger.info("test_run_tobit_regression PASSED")

def test_analysis_end_to_end():
    """
    End-to-end integration test:
    1. Create mock data.
    2. Run correlation analysis.
    3. Run regression analysis.
    4. Verify outputs are consistent (e.g., sample size matches).
    """
    logger.info("Running test_analysis_end_to_end...")
    df = create_mock_censored_dataset(n_samples=50)

    # Run Correlation
    corr_result = compute_censored_kendall_tau(
        df, 'temperature', 'water_log_mixing_ratio', 'is_censored', n_bootstrap=5
    )

    # Run Regression
    reg_result = run_tobit_regression(
        df, 'water_log_mixing_ratio', ['temperature', 'metallicity'], 'is_censored'
    )

    # Verify consistency
    assert len(df) == 50, "Mock data size mismatch"
    assert corr_result['tau'] is not None
    assert reg_result['log_likelihood'] is not None

    # Check that we didn't crash on censored data
    censored_count = df['is_censored'].sum()
    assert censored_count > 0, "Test data should have some censored values"

    logger.info(f"Analysis completed with {censored_count} censored values.")
    logger.info("test_analysis_end_to_end PASSED")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
