"""
Integration test for robustness check execution (T030).

This test verifies that the robustness checks (leave-one-region-out and bootstrap)
defined in code/analysis/robustness.py execute correctly and produce valid outputs
as specified in User Story 3.

Prerequisites:
- T023: Mixed-Effects Model implementation (code/analysis/model.py)
- T026: Robustness check logic implementation (code/analysis/model.py)

This test must run AFTER the data pipeline has generated the processed dataset.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import numpy as np
import pytest
from statsmodels.formula.api import mixedlm

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.model import run_robustness_checks, calculate_fdr_adjusted_pvalues
from utils.config import get_processed_data_dir, get_state_dir
from utils.logging import initialize_logging, get_provenance_summary

# Constants
EXPECTED_ROBUSTNESS_METRICS = [
    "leave_one_region_out",
    "bootstrap_resampling",
    "variance_in_significance_rates",
    "convergence_time",
    "retries_attempted"
]

MIN_BOOTSTRAP_ITERATIONS = 100  # Reduced for CI speed, but > 0


@pytest.fixture(scope="module")
def setup_test_environment():
    """Setup temporary directories and logging for the test."""
    # Initialize logging
    log_dir = project_root / "state" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    initialize_logging(log_dir=log_dir)
    
    # Ensure data directories exist
    processed_dir = get_processed_data_dir()
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    state_dir = get_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    
    return {
        "processed_dir": processed_dir,
        "state_dir": state_dir,
        "log_dir": log_dir
    }


@pytest.fixture(scope="module")
def sample_processed_data(setup_test_environment):
    """
    Create or load a sample processed dataset for testing.
    
    If the real processed dataset exists, load it. Otherwise, create a minimal
    synthetic dataset that matches the expected schema for robustness testing.
    
    NOTE: This is a TEST ONLY fixture. In production, the real data pipeline
    must generate this file. We create synthetic data here to ensure the test
    can run in CI without requiring the full data download pipeline.
    """
    data_path = setup_test_environment["processed_dir"] / "merged_sample.parquet"
    
    # Check if real data exists
    if data_path.exists():
        try:
            df = pd.read_parquet(data_path)
            # Validate schema
            required_cols = ["country", "year", "household_id", "csa_index", 
                             "food_security_score", "digital_access", "finance_access",
                             "region", "sample_weight"]
            if all(col in df.columns for col in required_cols):
                return df
        except Exception as e:
            pytest.skip(f"Real data file exists but is invalid: {e}")
    
    # Create minimal synthetic dataset for testing
    # This is ONLY for integration testing - not for actual research
    np.random.seed(42)
    n_samples = 500  # Small sample for CI speed
    
    countries = ["KEN", "IND", "VNM"]
    regions = ["East", "West", "North", "South"]
    
    data = {
        "country": np.random.choice(countries, n_samples),
        "year": np.random.choice([2020, 2021, 2022], n_samples),
        "household_id": range(n_samples),
        "csa_index": np.random.uniform(0, 1, n_samples),
        "food_security_score": np.random.uniform(0, 100, n_samples),
        "digital_access": np.random.uniform(0, 1, n_samples),
        "finance_access": np.random.uniform(0, 1, n_samples),
        "region": np.random.choice(regions, n_samples),
        "sample_weight": np.random.uniform(0.5, 1.5, n_samples),
        "latitude": np.random.uniform(-10, 20, n_samples),
        "longitude": np.random.uniform(20, 100, n_samples),
    }
    
    df = pd.DataFrame(data)
    df.to_parquet(data_path, index=False)
    
    return df


def test_robustness_checks_execution(sample_processed_data, setup_test_environment):
    """
    Test that robustness checks execute without errors and produce valid outputs.
    
    This is the main integration test for T030. It verifies:
    1. The run_robustness_checks function executes successfully
    2. All expected metrics are computed
    3. Output files are created in the correct locations
    4. Results are statistically valid (non-empty, reasonable ranges)
    """
    # Define output paths
    output_dir = setup_test_environment["state_dir"] / "robustness_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_path = output_dir / "robustness_results.json"
    logs_path = output_dir / "robustness_log.json"
    
    # Run robustness checks
    try:
        results = run_robustness_checks(
            data=sample_processed_data,
            output_dir=output_dir,
            bootstrap_iterations=MIN_BOOTSTRAP_ITERATIONS,
            timeout_hours=0.5  # Short timeout for CI
        )
    except Exception as e:
        pytest.fail(f"run_robustness_checks failed with exception: {e}")
    
    # Verify results structure
    assert isinstance(results, dict), "Results must be a dictionary"
    
    # Check for expected metrics
    for metric in EXPECTED_ROBUSTNESS_METRICS:
        assert metric in results, f"Missing expected metric: {metric}"
    
    # Verify leave-one-region-out results
    if "leave_one_region_out" in results:
        lolo_results = results["leave_one_region_out"]
        assert isinstance(lolo_results, dict), "leave_one_region_out must be a dict"
        assert len(lolo_results) > 0, "leave_one_region_out must have at least one result"
        
        # Check that each region was excluded
        excluded_regions = [key for key in lolo_results.keys() if key.startswith("exclude_")]
        assert len(excluded_regions) > 0, "At least one region should be excluded"
        
        # Verify each exclusion result has required fields
        for region_key, region_results in lolo_results.items():
            assert "coefficients" in region_results, f"{region_key} missing coefficients"
            assert "p_values" in region_results, f"{region_key} missing p_values"
            assert "variance" in region_results, f"{region_key} missing variance"
    
    # Verify bootstrap resampling results
    if "bootstrap_resampling" in results:
        bootstrap_results = results["bootstrap_resampling"]
        assert isinstance(bootstrap_results, dict), "bootstrap_resampling must be a dict"
        assert "iterations" in bootstrap_results, "Missing iterations count"
        assert bootstrap_results["iterations"] >= MIN_BOOTSTRAP_ITERATIONS, \
            f"Bootstrap iterations ({bootstrap_results['iterations']}) < minimum ({MIN_BOOTSTRAP_ITERATIONS})"
        
        assert "mean_coefficients" in bootstrap_results, "Missing mean_coefficients"
        assert "std_coefficients" in bootstrap_results, "Missing std_coefficients"
        assert "confidence_intervals" in bootstrap_results, "Missing confidence_intervals"
        
        # Verify confidence intervals are reasonable
        for ci_key, ci_values in bootstrap_results["confidence_intervals"].items():
            assert len(ci_values) == 2, f"Confidence interval for {ci_key} must have 2 values"
            assert ci_values[0] <= ci_values[1], f"Invalid CI for {ci_key}: {ci_values}"
    
    # Verify variance in significance rates
    if "variance_in_significance_rates" in results:
        variance_results = results["variance_in_significance_rates"]
        assert isinstance(variance_results, dict), "variance_in_significance_rates must be a dict"
        assert "threshold_sweep" in variance_results, "Missing threshold_sweep"
        
        # Check that variance was calculated for different thresholds
        thresholds = variance_results["threshold_sweep"]
        assert len(thresholds) > 1, "Must test at least 2 different thresholds"
        
        for threshold, significance_rate in thresholds.items():
            assert 0 <= significance_rate <= 1, \
                f"Invalid significance rate for threshold {threshold}: {significance_rate}"
    
    # Verify convergence time and retries
    assert "convergence_time" in results, "Missing convergence_time"
    assert isinstance(results["convergence_time"], (int, float)), "convergence_time must be numeric"
    assert results["convergence_time"] >= 0, "convergence_time must be non-negative"
    
    assert "retries_attempted" in results, "Missing retries_attempted"
    assert isinstance(results["retries_attempted"], int), "retries_attempted must be integer"
    assert results["retries_attempted"] >= 0, "retries_attempted must be non-negative"
    
    # Verify output files were created
    assert results_path.exists(), f"Results file not created: {results_path}"
    assert logs_path.exists(), f"Log file not created: {logs_path}"
    
    # Verify file contents are valid JSON
    try:
        with open(results_path, 'r') as f:
            file_results = json.load(f)
        assert file_results == results, "File contents don't match returned results"
    except json.JSONDecodeError as e:
        pytest.fail(f"Results file is not valid JSON: {e}")
    
    try:
        with open(logs_path, 'r') as f:
            log_contents = json.load(f)
        assert isinstance(log_contents, dict), "Log file must contain a dictionary"
    except json.JSONDecodeError as e:
        pytest.fail(f"Log file is not valid JSON: {e}")
    
    # Verify provenance logging
    provenance_summary = get_provenance_summary()
    assert provenance_summary is not None, "Provenance summary should exist"
    assert len(provenance_summary) > 0, "Provenance summary should not be empty"

def test_robustness_output_schema_compliance(sample_processed_data, setup_test_environment):
    """
    Test that robustness output files comply with the expected schema.
    
    This test verifies the structure and data types of the output files
    to ensure they match the research specification.
    """
    output_dir = setup_test_environment["state_dir"] / "robustness_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_path = output_dir / "robustness_results.json"
    
    # Run robustness checks if results don't exist
    if not results_path.exists():
        results = run_robustness_checks(
            data=sample_processed_data,
            output_dir=output_dir,
            bootstrap_iterations=MIN_BOOTSTRAP_ITERATIONS,
            timeout_hours=0.5
        )
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
    else:
        with open(results_path, 'r') as f:
            results = json.load(f)
    
    # Schema validation
    schema_checks = {
        "top_level_keys": [
            "leave_one_region_out",
            "bootstrap_resampling",
            "variance_in_significance_rates",
            "convergence_time",
            "retries_attempted",
            "metadata"
        ],
        "metadata_fields": [
            "timestamp",
            "data_source",
            "model_specification",
            "bootstrap_iterations",
            "timeout_hours"
        ],
        "bootstrap_fields": [
            "iterations",
            "mean_coefficients",
            "std_coefficients",
            "confidence_intervals",
            "convergence_status"
        ]
    }
    
    # Check top-level keys
    for key in schema_checks["top_level_keys"]:
        assert key in results, f"Missing top-level key: {key}"
    
    # Check metadata
    assert "metadata" in results, "Missing metadata section"
    for field in schema_checks["metadata_fields"]:
        assert field in results["metadata"], f"Missing metadata field: {field}"
    
    # Check bootstrap structure
    bootstrap = results.get("bootstrap_resampling", {})
    for field in schema_checks["bootstrap_fields"]:
        assert field in bootstrap, f"Missing bootstrap field: {field}"
    
    # Verify data types
    assert isinstance(results["convergence_time"], (int, float)), "convergence_time must be numeric"
    assert isinstance(results["retries_attempted"], int), "retries_attempted must be integer"
    assert isinstance(results["bootstrap_resampling"]["iterations"], int), "iterations must be integer"
    
    # Verify coefficient structure
    mean_coefs = bootstrap.get("mean_coefficients", {})
    std_coefs = bootstrap.get("std_coefficients", {})
    
    assert set(mean_coefs.keys()) == set(std_coefs.keys()), \
        "mean_coefficients and std_coefficients must have same keys"
    
    # Verify confidence intervals
    cis = bootstrap.get("confidence_intervals", {})
    for var_name, ci in cis.items():
        assert isinstance(ci, list) and len(ci) == 2, \
            f"Confidence interval for {var_name} must be a list of 2 values"
        assert all(isinstance(v, (int, float)) for v in ci), \
            f"Confidence interval values must be numeric"

def test_robustness_with_timeout_handling(sample_processed_data, setup_test_environment):
    """
    Test that timeout handling works correctly during robustness checks.
    
    This test verifies that the system can handle timeouts gracefully,
    log state, and attempt reduced-batch retries as specified in T027.
    """
    output_dir = setup_test_environment["state_dir"] / "robustness_timeout_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Use a very short timeout to trigger timeout handling
    results = run_robustness_checks(
        data=sample_processed_data,
        output_dir=output_dir,
        bootstrap_iterations=MIN_BOOTSTRAP_ITERATIONS,
        timeout_hours=0.01  # Very short timeout to trigger handling
    )
    
    # Verify that timeout was handled
    assert "convergence_time" in results, "Missing convergence_time"
    assert "retries_attempted" in results, "Missing retries_attempted"
    
    # Verify that results were still produced (even if partial)
    assert "leave_one_region_out" in results or "bootstrap_resampling" in results, \
        "At least one robustness check should have completed"
    
    # Verify logs were created
    logs_path = output_dir / "robustness_log.json"
    assert logs_path.exists(), "Log file should be created even on timeout"
    
    with open(logs_path, 'r') as f:
        log_contents = json.load(f)
    
    assert "timeout_handled" in log_contents or "status" in log_contents, \
        "Log should indicate timeout was handled"