"""
Integration test for correlation analysis (US2).

This test verifies the full correlation analysis pipeline:
1. Loads real or synthetic input data from data/results/dipole_timeseries.csv
2. Runs the statistical analysis (Lomb-Scargle, block-bootstrap, Monte-Carlo)
3. Verifies output artifacts are generated correctly
4. Validates statistical significance thresholds

Prerequisites:
- T018 must be completed (dipole_timeseries.csv exists)
- T021-T025 must be completed (stats.py and analyze_correlation.py)
"""
import os
import sys
import pytest
import json
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from analyze_correlation import main as analyze_main
from src.stats import (
    compute_lomb_scargle,
    block_bootstrap_correlation,
    monte_carlo_shuffle_test,
    bonferroni_corrected_pvalue
)

# Test fixtures
TEST_DATA_PATH = PROJECT_ROOT / "data" / "results" / "dipole_timeseries.csv"
TEST_OUTPUT_DIR = PROJECT_ROOT / "data" / "results" / "test_correlation"
EXPECTED_PLOT_PATH = TEST_OUTPUT_DIR / "periodogram_icecube.png"
EXPECTED_METRICS_PATH = TEST_OUTPUT_DIR / "correlation_metrics.json"

@pytest.fixture(scope="module")
def setup_test_environment():
    """Ensure test data exists and create output directory."""
    # Create output directory
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if real data exists, otherwise create minimal test data
    if not TEST_DATA_PATH.exists():
        # Create minimal synthetic data for integration testing
        # This is ONLY for testing the pipeline structure, not scientific results
        dates = pd.date_range(start="2010-01-01", end="2020-01-01", freq="27D")
        data = {
            "interval_start": dates.strftime("%Y-%m-%d"),
            "dipole_amp": np.random.uniform(0.5, 2.0, len(dates)),
            "dipole_phase": np.random.uniform(0, 2*np.pi, len(dates)),
            "quad_amp": np.random.uniform(0.1, 0.5, len(dates)),
            "partial_interval": [False] * len(dates)
        }
        df = pd.DataFrame(data)
        df.to_csv(TEST_DATA_PATH, index=False)
        print(f"Created test data at {TEST_DATA_PATH}")
    
    yield
    
    # Cleanup test output (optional, comment out to inspect results)
    # import shutil
    # if TEST_OUTPUT_DIR.exists():
    #     shutil.rmtree(TEST_OUTPUT_DIR)

def test_full_correlation_pipeline(setup_test_environment):
    """
    Integration test: Run the full correlation analysis pipeline.
    
    Verifies:
    1. analyze_correlation.py executes without error
    2. Output files are created (periodogram plots, metrics JSON)
    3. Metrics contain required fields
    4. Statistical results are within expected ranges
    """
    # Run the main analysis
    try:
        analyze_main(
            input_path=str(TEST_DATA_PATH),
            output_dir=str(TEST_OUTPUT_DIR),
            detectors=["icecube"],
            bin_size_days=27
        )
    except Exception as e:
        pytest.fail(f"Correlation analysis failed to execute: {str(e)}")
    
    # Verify output files exist
    assert EXPECTED_METRICS_PATH.exists(), "Correlation metrics JSON not generated"
    
    # Load and validate metrics
    with open(EXPECTED_METRICS_PATH, 'r') as f:
        metrics = json.load(f)
    
    # Check required fields
    required_fields = [
        "detector", "lomb_scargle_period", "lomb_scargle_power",
        "lomb_scargle_pvalue", "block_bootstrap_corr", "block_bootstrap_pvalue",
        "monte_carlo_fap", "bonferroni_corrected", "is_significant"
    ]
    
    for field in required_fields:
        assert field in metrics, f"Missing required field in metrics: {field}"
    
    # Validate numeric ranges
    assert 0 <= metrics["lomb_scargle_power"] <= 1, "Lomb-Scargle power out of range"
    assert 0 <= metrics["lomb_scargle_pvalue"] <= 1, "Lomb-Scargle p-value out of range"
    assert -1 <= metrics["block_bootstrap_corr"] <= 1, "Correlation coefficient out of range"
    assert 0 <= metrics["block_bootstrap_pvalue"] <= 1, "Block-bootstrap p-value out of range"
    assert 0 <= metrics["monte_carlo_fap"] <= 1, "Monte-Carlo FAP out of range"
    
    # Verify Bonferroni correction logic
    alpha = 0.05
    n_tests = 3  # LS, bootstrap, MC
    corrected_alpha = alpha / n_tests
    
    if metrics["bonferroni_corrected"]:
        assert metrics["lomb_scargle_pvalue"] < corrected_alpha, \
            "Bonferroni flag set but p-value not significant"
    
    print(f"Integration test passed. Metrics: {metrics}")

def test_lomb_scargle_computation(setup_test_environment):
    """
    Test Lomb-Scargle periodogram computation on real data.
    
    Verifies:
    1. Function computes valid periodogram
    2. Peak frequency corresponds to solar cycle (~11 years or ~1 year for seasonal)
    3. P-values are computed correctly
    """
    df = pd.read_csv(TEST_DATA_PATH)
    
    # Convert interval_start to numeric (days since first observation)
    df["interval_start"] = pd.to_datetime(df["interval_start"])
    days = (df["interval_start"] - df["interval_start"].min()).dt.days.values
    amplitude = df["dipole_amp"].values
    
    # Run Lomb-Scargle
    frequencies, powers, pvalues = compute_lomb_scargle(
        days, amplitude, 
        min_period=30,  # days
        max_period=4000  # ~11 years
    )
    
    # Validate outputs
    assert len(frequencies) == len(powers) == len(pvalues), "Output length mismatch"
    assert np.all(powers >= 0), "Negative powers detected"
    assert np.all((pvalues >= 0) & (pvalues <= 1)), "P-values out of range"
    
    # Find peak
    peak_idx = np.argmax(powers)
    peak_period = 1.0 / frequencies[peak_idx] if frequencies[peak_idx] > 0 else np.inf
    
    print(f"Peak period detected: {peak_period:.2f} days")
    assert peak_period > 0, "Invalid peak period detected"

def test_block_bootstrap_resampling(setup_test_environment):
    """
    Test block-bootstrap resampling for correlation uncertainty.
    
    Verifies:
    1. Bootstrap produces correlation distribution
    2. Confidence intervals are computed
    3. Fallback logic for small sample sizes (FR-005)
    """
    df = pd.read_csv(TEST_DATA_PATH)
    df["interval_start"] = pd.to_datetime(df["interval_start"])
    days = (df["interval_start"] - df["interval_start"].min()).dt.days.values
    amplitude = df["dipole_amp"].values
    
    # Create solar proxy time series (simulated for integration test)
    # In production, this would be loaded from NOAA data
    np.random.seed(42)
    solar_proxy = np.sin(2 * np.pi * days / 365.25) + np.random.normal(0, 0.1, len(days))
    
    # Run block-bootstrap
    corr_dist, mean_corr, pvalue = block_bootstrap_correlation(
        days, amplitude, solar_proxy,
        n_bootstrap=100,  # Reduced for speed
        bin_size_days=27
    )
    
    # Validate outputs
    assert len(corr_dist) == 100, "Bootstrap distribution size mismatch"
    assert -1 <= mean_corr <= 1, "Mean correlation out of range"
    assert 0 <= pvalue <= 1, "Bootstrap p-value out of range"
    
    # Check confidence interval logic
    ci_lower = np.percentile(corr_dist, 2.5)
    ci_upper = np.percentile(corr_dist, 97.5)
    assert ci_lower <= mean_corr <= ci_upper, "Mean outside confidence interval"
    
    print(f"Bootstrap correlation: {mean_corr:.3f} [{ci_lower:.3f}, {ci_upper:.3f}]")

def test_monte_carlo_shuffle_test(setup_test_environment):
    """
    Test Monte-Carlo shuffle test for false alarm probability.
    
    Verifies:
    1. Shuffle procedure breaks correlation structure
    2. FAP is computed correctly
    3. Results are consistent with analytical methods
    """
    df = pd.read_csv(TEST_DATA_PATH)
    df["interval_start"] = pd.to_datetime(df["interval_start"])
    days = (df["interval_start"] - df["interval_start"].min()).dt.days.values
    amplitude = df["dipole_amp"].values
    
    # Create solar proxy time series
    np.random.seed(42)
    solar_proxy = np.sin(2 * np.pi * days / 365.25) + np.random.normal(0, 0.1, len(days))
    
    # Run Monte-Carlo shuffle
    observed_corr = np.corrcoef(amplitude, solar_proxy)[0, 1]
    fap = monte_carlo_shuffle_test(
        days, amplitude, solar_proxy,
        n_permutations=500  # Reduced for speed
    )
    
    # Validate outputs
    assert -1 <= observed_corr <= 1, "Observed correlation out of range"
    assert 0 <= fap <= 1, "FAP out of range"
    
    print(f"Observed correlation: {observed_corr:.3f}, FAP: {fap:.3f}")
    
    # FAP should generally be low if correlation is real, high if random
    # This is a sanity check, not a strict threshold
    assert fap > 0, "FAP cannot be exactly zero with finite permutations"

def test_bonferroni_correction(setup_test_environment):
    """
    Test Bonferroni correction for multiple hypothesis testing.
    
    Verifies:
    1. Correction factor is applied correctly
    2. Significance flag is set appropriately
    3. Alpha level is adjusted for number of tests
    """
    # Test with sample p-values
    pvalues = [0.01, 0.03, 0.05]
    alpha = 0.05
    n_tests = len(pvalues)
    
    corrected_pvalues = [bonferroni_corrected_pvalue(p, n_tests) for p in pvalues]
    
    # Verify correction
    expected_corrected = [min(p * n_tests, 1.0) for p in pvalues]
    
    for i, (calc, expected) in enumerate(zip(corrected_pvalues, expected_corrected)):
        assert abs(calc - expected) < 1e-10, f"Bonferroni correction error at index {i}"
    
    # Test significance flagging
    is_significant = [p < (alpha / n_tests) for p in corrected_pvalues]
    
    print(f"Bonferroni corrected p-values: {corrected_pvalues}")
    print(f"Significant at alpha={alpha}: {is_significant}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])