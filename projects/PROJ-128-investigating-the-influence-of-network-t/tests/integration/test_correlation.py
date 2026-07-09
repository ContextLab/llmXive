"""
Integration test for end-to-end correlation analysis (User Story 2).

This test verifies that the full correlation pipeline:
1. Loads the structural and dynamic metrics CSVs produced by US1.
2. Performs normality testing to select the correct correlation method.
3. Calculates correlations between structural and dynamic metrics.
4. Applies Benjamini-Hochberg FDR correction.
5. Writes the results to `data/processed/correlation_results.csv`.

It asserts that the output file exists, contains the expected columns,
and that the statistical logic (normality check -> correlation choice)
executes without error on real data.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from config import ensure_directories
from analysis.correlation import (
    check_normality,
    calculate_correlation,
    benjamini_hochberg_fdr,
    run_correlation_analysis,
    main as correlation_main
)


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory structure mimicking the project layout."""
    temp_dir = tempfile.mkdtemp()
    # Recreate expected subdirectories
    dirs = [
        "code", "data", "data/raw", "data/processed", "data/logs",
        "contracts", "tests", "tests/integration"
    ]
    for d in dirs:
        os.makedirs(os.path.join(temp_dir, d), exist_ok=True)
    return temp_dir


def generate_mock_metrics_csvs(temp_dir: str):
    """
    Generates realistic mock data for structural and dynamic metrics.
    In a real CI environment with full data, this would load from data/processed.
    For this integration test, we generate deterministic mock data that
    satisfies the schema and allows the correlation logic to run.
    """
    n_subjects = 30
    np.random.seed(42)

    # Structural Metrics (Simulated real values)
    # Global Efficiency: typically 0.3 - 0.6
    # Clustering Coeff: typically 0.2 - 0.5
    # Modularity: typically 0.3 - 0.7
    struct_data = {
        "subject_id": [f"sub-{i:03d}" for i in range(n_subjects)],
        "global_efficiency": np.random.uniform(0.35, 0.55, n_subjects),
        "clustering_coeff": np.random.uniform(0.25, 0.45, n_subjects),
        "modularity": np.random.uniform(0.35, 0.65, n_subjects)
    }
    # Introduce a slight correlation for testing purposes
    # Let's make global_efficiency slightly correlated with dwell_time
    struct_df = pd.DataFrame(struct_data)

    # Dynamic Metrics (Simulated real values)
    # Dwell Time: typically 100 - 500 ms (or arbitrary units)
    # Visited States: typically 3 - 5
    # We will create a slight dependency on global_efficiency to ensure a non-zero correlation
    base_dwell = 200 + (struct_df["global_efficiency"] - 0.4) * 500
    dynamic_data = {
        "subject_id": [f"sub-{i:03d}" for i in range(n_subjects)],
        "dwell_time": base_dwell + np.random.normal(0, 20, n_subjects),
        "visited_states": np.random.choice([3, 4, 5], n_subjects)
    }
    dynamic_df = pd.DataFrame(dynamic_data)

    # Ensure directories exist
    ensure_directories(temp_dir)

    # Save CSVs
    struct_path = os.path.join(temp_dir, "data", "processed", "structural_metrics.csv")
    dynamic_path = os.path.join(temp_dir, "data", "processed", "dynamic_metrics.csv")

    struct_df.to_csv(struct_path, index=False)
    dynamic_df.to_csv(dynamic_path, index=False)

    return struct_path, dynamic_path


def test_normality_check_logic():
    """Test that normality check correctly identifies distribution types."""
    # Normal distribution
    normal_data = np.random.normal(loc=0, scale=1, size=100)
    is_normal, stat, p = check_normality(normal_data)
    assert is_normal is True, "Normal data should pass Shapiro-Wilk test"
    assert p > 0.05, "P-value for normal data should be > 0.05"

    # Skewed distribution (exponential)
    skewed_data = np.random.exponential(scale=2.0, size=100)
    is_normal_skewed, stat_skewed, p_skewed = check_normality(skewed_data)
    assert is_normal_skewed is False, "Skewed data should fail Shapiro-Wilk test"
    assert p_skewed < 0.05, "P-value for skewed data should be < 0.05"


def test_benjamini_hochberg_fdr_logic():
    """Test FDR correction logic."""
    # Known p-values
    p_values = np.array([0.001, 0.01, 0.02, 0.04, 0.06, 0.10])
    q = 0.05
    corrected = benjamini_hochberg_fdr(p_values, q)

    assert len(corrected) == len(p_values)
    # The smallest p-value (0.001) should definitely be significant (corrected < 0.05)
    # The largest (0.10) might not be
    assert corrected[0] < 0.05, "Smallest p-value should be significant after FDR"
    # Verify monotonicity: corrected p-values should be non-decreasing
    assert np.all(np.diff(corrected) >= -1e-9), "Corrected p-values should be monotonic"


def test_integration_end_to_end_correlation(temp_project_dir):
    """
    End-to-end integration test:
    1. Generate mock data (simulating US1 output).
    2. Run the full correlation analysis pipeline.
    3. Verify output file exists and contains correct columns.
    4. Verify that the logic selected the correct correlation method.
    """
    # 1. Setup data
    struct_path, dynamic_path = generate_mock_metrics_csvs(temp_project_dir)

    # Verify input files exist
    assert os.path.exists(struct_path), "Structural metrics CSV not created"
    assert os.path.exists(dynamic_path), "Dynamic metrics CSV not created"

    # 2. Run the analysis
    # We call the function directly to avoid CLI parsing in a test
    output_path = os.path.join(temp_project_dir, "data", "processed", "correlation_results.csv")

    try:
        results_df = run_correlation_analysis(
            struct_path=struct_path,
            dynamic_path=dynamic_path,
            output_path=output_path
        )
    except Exception as e:
        pytest.fail(f"Correlation analysis failed: {e}")

    # 3. Verify output file exists
    assert os.path.exists(output_path), "Correlation results CSV was not written to disk"

    # 4. Verify content structure
    assert results_df is not None, "Function did not return a DataFrame"
    expected_columns = [
        "structural_metric", "dynamic_metric", "correlation_method",
        "r_value", "p_value", "fdr_corrected_p", "is_significant"
    ]
    for col in expected_columns:
        assert col in results_df.columns, f"Missing column: {col}"

    # 5. Verify data integrity
    assert len(results_df) > 0, "Results DataFrame is empty"
    assert results_df["r_value"].notna().all(), "r_values contain NaN"
    assert results_df["p_value"].notna().all(), "p_values contain NaN"
    assert results_df["fdr_corrected_p"].notna().all(), "FDR p_values contain NaN"

    # 6. Verify logic selection (Pearson vs Spearman)
    # Our mock data is roughly normal, so it should likely use Pearson
    # But we just assert that a method was chosen
    assert results_df["correlation_method"].isin(["pearson", "spearman"]).all(), \
        "Invalid correlation method selected"

    # 7. Verify FDR calculation
    # If we have significant findings, FDR should be calculated
    significant_rows = results_df[results_df["is_significant"]]
    if len(significant_rows) > 0:
        # At least one should have fdr_corrected_p < 0.05
        assert (significant_rows["fdr_corrected_p"] < 0.05).any(), \
            "Significant rows should have fdr_corrected_p < 0.05"

def test_main_entry_point(temp_project_dir):
    """
    Test the CLI main entry point to ensure it can be invoked as a script.
    """
    # Setup data first
    generate_mock_metrics_csvs(temp_project_dir)

    # Prepare arguments for main
    # We simulate running: python -m code.analysis.correlation
    # But since we are in a test, we call the function with args
    import sys
    original_argv = sys.argv

    try:
        sys.argv = [
            "correlation.py",
            "--struct-csv", os.path.join(temp_project_dir, "data", "processed", "structural_metrics.csv"),
            "--dyn-csv", os.path.join(temp_project_dir, "data", "processed", "dynamic_metrics.csv"),
            "--output", os.path.join(temp_project_dir, "data", "processed", "correlation_results.csv")
        ]

        # Run the main function
        correlation_main()

        # Verify output
        output_path = os.path.join(temp_project_dir, "data", "processed", "correlation_results.csv")
        assert os.path.exists(output_path), "Main entry point did not create output file"

        df = pd.read_csv(output_path)
        assert "r_value" in df.columns, "Output missing r_value column"

    finally:
        sys.argv = original_argv

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
