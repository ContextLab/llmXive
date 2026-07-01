"""Integration test for report generation (T022).

This test verifies that the full simulation pipeline (with reduced iterations)
correctly generates a final report containing rows for all required alpha levels.
"""
import os
import tempfile
import shutil
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
import sys
sys.path.insert(0, str(project_root / "code"))

from simulation_runner import run_robust_simulation
from analysis import aggregate_errors
from config import load_config, set_seed, ALPHA_LEVELS


def test_report_contains_all_alpha_levels():
    """
    Integration test: Runs the full simulation with reduced iterations and asserts
    that the generated final_report.csv contains rows for alpha = 0.01, 0.05, 0.10.
    """
    # Create a temporary directory for output artifacts
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()

    try:
        os.chdir(temp_dir)

        # Configuration for reduced iteration test
        n_iterations = 5  # Reduced for speed in integration test
        icc_value = 0.1
        seed = 42

        # Ensure output directory exists
        derived_dir = Path(temp_dir) / "data" / "derived"
        derived_dir.mkdir(parents=True, exist_ok=True)

        # Set seed for reproducibility
        set_seed(seed)

        # Run the robust simulation
        # Returns a list of result dictionaries
        results = run_robust_simulation(
            icc=icc_value,
            n_iterations=n_iterations,
            seed=seed
        )

        # Aggregate errors
        # This function expects a list of dicts and alpha_levels
        # It returns a DataFrame with columns: method, icc, alpha, error_rate, ci_lower, ci_upper
        df_results = aggregate_errors(results, ALPHA_LEVELS)

        # Write the final report
        report_path = derived_dir / "final_report.csv"
        df_results.to_csv(report_path, index=False)

        # Verify the file exists
        assert report_path.exists(), f"Report file {report_path} was not created."

        # Load and verify content
        report_df = pd.read_csv(report_path)

        # Required alpha levels per T022
        required_alphas = [0.01, 0.05, 0.10]

        # Check that all required alpha levels are present in the 'alpha' column
        # Note: The column name from aggregate_errors is 'alpha'
        found_alphas = set(report_df['alpha'].unique())
        
        for alpha in required_alphas:
            assert alpha in found_alphas, (
                f"Report is missing rows for alpha = {alpha}. "
                f"Found alphas: {found_alphas}"
            )

        # Additional sanity check: ensure we have rows for each method
        expected_methods = {'naive', 'cluster_robust', 'block_permutation'}
        found_methods = set(report_df['method'].unique())
        for method in expected_methods:
            assert method in found_methods, (
                f"Report is missing rows for method = {method}. "
                f"Found methods: {found_methods}"
            )

    finally:
        # Cleanup
        os.chdir(original_cwd)
        shutil.rmtree(temp_dir)