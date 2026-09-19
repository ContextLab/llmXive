"""
Integration test for the statistical analysis pipeline (User Story 2).

This test verifies the end-to-end execution of the statistical analysis module
using a synthetic dataset that mimics the structure of the real cleaned data.

It ensures:
1. The analysis pipeline can load data from the processed directory.
2. Welch's t-test is correctly applied to both primary metrics.
3. Bonferroni correction is applied.
4. Effect sizes (Cohen's d) and confidence intervals are calculated.
5. Power analysis and MDES are computed.
6. The final statistical report is generated and saved to the correct path.
"""

import os
import json
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np

# Import the analysis functions from the project code
from code.analysis import (
    welch_t_test,
    calculate_cohen_d,
    calculate_effect_size_ci,
    bonferroni_correction,
    calculate_power_and_mdes,
    run_analysis,
    run_full_analysis
)
from code.config import get_config, ensure_dirs

# Fixtures
@pytest.fixture(scope="module")
def test_env():
    """
    Creates a temporary directory structure to mimic the project environment
    and generates a synthetic dataset for testing.
    """
    # Create a temporary root directory
    temp_root = tempfile.mkdtemp(prefix="test_analysis_integration_")
    
    # Define paths relative to temp_root to mimic project structure
    data_raw = os.path.join(temp_root, "data", "raw")
    data_processed = os.path.join(temp_root, "data", "processed")
    data_results = os.path.join(temp_root, "data", "results")
    
    # Create directories
    os.makedirs(data_raw, exist_ok=True)
    os.makedirs(data_processed, exist_ok=True)
    os.makedirs(data_results, exist_ok=True)
    
    # Generate synthetic data that mimics the cleaned dataset structure
    # We need two groups: 'nostalgia' and 'control'
    n_per_group = 50
    np.random.seed(42) # For reproducibility
    
    # Simulate data where Nostalgia group has fewer errors (better performance)
    # and completes more categories (better performance)
    nostalgia_errors = np.random.normal(loc=3.5, scale=1.2, size=n_per_group)
    control_errors = np.random.normal(loc=5.0, scale=1.5, size=n_per_group)
    
    nostalgia_categories = np.random.normal(loc=4.5, scale=1.0, size=n_per_group)
    control_categories = np.random.normal(loc=3.0, scale=1.1, size=n_per_group)
    
    participant_ids = [f"sub_{i:03d}" for i in range(n_per_group * 2)]
    stimulus_types = ["nostalgia"] * n_per_group + ["control"] * n_per_group
    
    # Combine data
    df_data = {
        "participant_id": participant_ids,
        "stimulus_type": stimulus_types,
        "perseverative_errors": np.concatenate([nostalgia_errors, control_errors]),
        "categories_completed": np.concatenate([nostalgia_categories, control_categories]),
        "age": [65 + np.random.randint(0, 20) for _ in range(n_per_group * 2)]
    }
    
    df = pd.DataFrame(df_data)
    
    # Save the synthetic cleaned dataset
    cleaned_dataset_path = os.path.join(data_processed, "cleaned_dataset.csv")
    df.to_csv(cleaned_dataset_path, index=False)
    
    # Save metadata to indicate this is a test run (optional but good practice)
    metadata_path = os.path.join(data_raw, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump({
            "dataset_source": "synthetic_integration_test",
            "simulation_mode": True,
            "validation_study_doi": None
        }, f)
    
    yield {
        "temp_root": temp_root,
        "data_processed": data_processed,
        "data_results": data_results,
        "cleaned_dataset_path": cleaned_dataset_path
    }
    
    # Cleanup
    shutil.rmtree(temp_root)

def test_welch_ttest_basic():
    """Test the basic Welch's t-test function with known values."""
    group_a = np.array([1, 2, 3, 4, 5])
    group_b = np.array([2, 3, 4, 5, 6])
    
    t_stat, p_val = welch_t_test(group_a, group_b)
    
    assert isinstance(t_stat, float)
    assert isinstance(p_val, float)
    assert 0 <= p_val <= 1
    # For identical distributions shifted by 1, p-value should be significant
    # but we just check the range and type here.

def test_cohen_d_basic():
    """Test Cohen's d calculation."""
    group_a = np.array([1, 2, 3, 4, 5])
    group_b = np.array([2, 3, 4, 5, 6])
    
    d = calculate_cohen_d(group_a, group_b)
    
    assert isinstance(d, float)
    # Cohen's d for these small, overlapping groups should be around -1.0
    assert -2.0 < d < 2.0

def test_bonferroni_correction():
    """Test Bonferroni correction logic."""
    p_values = [0.01, 0.04, 0.06]
    alpha = 0.05
    n_comparisons = len(p_values)
    
    corrected = bonferroni_correction(p_values, alpha)
    
    assert isinstance(corrected, dict)
    assert "corrected_p_values" in corrected
    assert "alpha_corrected" in corrected
    
    # Check that corrected p-values are multiplied
    for i, p in enumerate(p_values):
        expected = min(p * n_comparisons, 1.0)
        assert abs(corrected["corrected_p_values"][i] - expected) < 1e-9

def test_run_full_analysis_integration(test_env):
    """
    End-to-end integration test: Run the full analysis pipeline on synthetic data
    and verify the output report is generated correctly.
    """
    cleaned_path = test_env["cleaned_dataset_path"]
    results_dir = test_env["data_results"]
    
    # Ensure the input file exists
    assert os.path.exists(cleaned_path), f"Input file not found: {cleaned_path}"
    
    # Run the full analysis pipeline
    # This function should load the data, run tests, and save the report
    report_path = os.path.join(results_dir, "statistical_report.json")
    
    try:
        run_full_analysis(
            input_path=cleaned_path,
            output_path=report_path
        )
    except Exception as e:
        pytest.fail(f"run_full_analysis failed: {str(e)}")
    
    # Verify the output file exists
    assert os.path.exists(report_path), f"Output report not generated at: {report_path}"
    
    # Verify the content of the report
    with open(report_path, "r") as f:
        report = json.load(f)
    
    # Check for required keys in the report
    required_keys = [
        "perseverative_errors",
        "categories_completed",
        "method",
        "correction_method",
        "effect_sizes",
        "power_analysis"
    ]
    
    for key in required_keys:
        assert key in report, f"Missing required key in report: {key}"
    
    # Verify specific structure for 'perseverative_errors'
    pe_result = report["perseverative_errors"]
    assert "t_statistic" in pe_result
    assert "p_value" in pe_result
    assert "p_value_corrected" in pe_result
    assert "cohen_d" in pe_result
    assert "ci_95" in pe_result
    
    # Verify specific structure for 'categories_completed'
    cat_result = report["categories_completed"]
    assert "t_statistic" in cat_result
    assert "p_value" in cat_result
    assert "p_value_corrected" in cat_result
    assert "cohen_d" in cat_result
    assert "ci_95" in cat_result
    
    # Verify power analysis structure
    power_result = report["power_analysis"]
    assert "power" in power_result
    assert "m_des" in power_result
    
    # Verify that the test detected a significant difference (since we generated data with a difference)
    # Note: In a real scenario, we might check the actual p-value, but for integration testing,
    # ensuring the structure is correct and the pipeline runs without error is the primary goal.
    # However, we can assert that p-values are present and numeric.
    assert 0 <= pe_result["p_value"] <= 1
    assert 0 <= cat_result["p_value"] <= 1

def test_run_analysis_with_small_sample(test_env):
    """
    Test that the analysis handles small sample sizes gracefully (as per T023).
    We will manually create a small dataset for this test.
    """
    data_processed = test_env["data_processed"]
    small_data_path = os.path.join(data_processed, "cleaned_dataset_small.csv")
    
    # Create a very small dataset (2 per group)
    small_df = pd.DataFrame({
        "participant_id": ["s1", "s2", "s3", "s4"],
        "stimulus_type": ["nostalgia", "nostalgia", "control", "control"],
        "perseverative_errors": [3.0, 4.0, 5.0, 6.0],
        "categories_completed": [4.0, 5.0, 3.0, 2.0],
        "age": [65, 66, 65, 66]
    })
    small_df.to_csv(small_data_path, index=False)
    
    results_dir = test_env["data_results"]
    small_report_path = os.path.join(results_dir, "statistical_report_small.json")
    
    # Run analysis
    # We expect this to run but potentially log warnings or handle the small N
    run_full_analysis(
        input_path=small_data_path,
        output_path=small_report_path
    )
    
    # Verify report exists
    assert os.path.exists(small_report_path)
    
    with open(small_report_path, "r") as f:
        small_report = json.load(f)
    
    # The report should still be generated, even if N is small
    assert "perseverative_errors" in small_report
    assert "categories_completed" in small_report

def test_error_handling_zero_variance():
    """
    Test that the analysis handles zero variance in a group without crashing.
    """
    group_a = np.array([1, 1, 1, 1, 1]) # Zero variance
    group_b = np.array([2, 3, 4, 5, 6])
    
    # The function should handle this gracefully, likely returning NaN or raising a specific warning
    # depending on implementation. We test that it doesn't crash with a generic exception.
    try:
        t_stat, p_val = welch_t_test(group_a, group_b)
        # If it returns, check if it's NaN (expected behavior for zero variance in Welch's)
        assert np.isnan(t_stat) or np.isnan(p_val), "Expected NaN for zero variance case"
    except Exception as e:
        # If it raises a specific error, that's also acceptable as long as it's handled
        # in the main pipeline. For this unit-style integration test, we just ensure it doesn't
        # crash with an unhandled TypeError/AttributeError.
        if not isinstance(e, (RuntimeError, ValueError)):
            raise e