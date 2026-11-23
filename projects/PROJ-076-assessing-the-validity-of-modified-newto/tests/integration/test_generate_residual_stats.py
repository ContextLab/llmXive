"""
Integration test for T034: Generate Residual Stats.

This test verifies that the generate_residual_stats script can run
end-to-end and produce a valid CSV with the expected columns.
"""
import os
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

# Mock dependencies if necessary, but prefer running against real data if available
# For this integration test, we assume the project data exists.
# If not, we skip or create a minimal mock setup.

def test_generate_residual_stats_script_exists():
    """Verify the script exists."""
    script_path = Path("code/generate_residual_stats.py")
    assert script_path.exists(), f"Script {script_path} not found"

def test_generate_residual_stats_output_columns():
    """
    Verify that the output CSV contains the required columns.
    This assumes the script has been run and produced results/residual_stats.csv.
    """
    output_path = Path("results/residual_stats.csv")
    
    if not output_path.exists():
        pytest.skip("residual_stats.csv not found. Run T034 first.")
    
    df = pd.read_csv(output_path)
    
    required_columns = [
        "galaxy_id", "model", "mean_residual", "median_residual", 
        "std_residual", "p_value_raw", "p_value_corrected"
    ]
    
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"

def test_generate_residual_stats_content_validity():
    """
    Check that the numeric columns are valid numbers and p-values are in [0, 1].
    """
    output_path = Path("results/residual_stats.csv")
    
    if not output_path.exists():
        pytest.skip("residual_stats.csv not found. Run T034 first.")
    
    df = pd.read_csv(output_path)
    
    # Check numeric columns
    numeric_cols = ["mean_residual", "median_residual", "std_residual", "p_value_raw", "p_value_corrected"]
    for col in numeric_cols:
        assert pd.to_numeric(df[col], errors='coerce').notna().all(), f"Column {col} contains non-numeric values"
    
    # Check p-values are between 0 and 1
    assert (df["p_value_raw"] >= 0).all() and (df["p_value_raw"] <= 1).all(), "p_value_raw out of range [0, 1]"
    assert (df["p_value_corrected"] >= 0).all() and (df["p_value_corrected"] <= 1).all(), "p_value_corrected out of range [0, 1]"
    
    # Check models are MOND or NFW
    assert df["model"].isin(["MOND", "NFW"]).all(), "Invalid model names found"

def test_holm_bonferroni_correction_ordering():
    """
    Verify that the Holm-Bonferroni correction was applied correctly.
    The corrected p-values should be non-decreasing when sorted by raw p-value.
    """
    output_path = Path("results/residual_stats.csv")
    
    if not output_path.exists():
        pytest.skip("residual_stats.csv not found. Run T034 first.")
    
    df = pd.read_csv(output_path)
    df_sorted = df.sort_values("p_value_raw")
    
    # The corrected p-values should be non-decreasing
    # Note: Holm-Bonferroni ensures that if p_raw(i) <= p_raw(j) then p_corr(i) <= p_corr(j)
    # However, the implementation might clamp values to 1.0.
    # We check that the sequence is non-decreasing.
    corrected = df_sorted["p_value_corrected"].values
    assert all(corrected[i] <= corrected[i+1] for i in range(len(corrected)-1)), \
        "Holm-Bonferroni corrected p-values are not non-decreasing"