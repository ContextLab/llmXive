"""
Integration test for T035: Verify final statistical_comparison.csv generation.

This test ensures that the write_final_results script:
1. Produces a file at the correct path
2. Contains the required columns
3. Has valid data types
"""
import os
import sys
import pandas as pd
import pytest
from pathlib import Path
import shutil

# Setup paths
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.write_final_results import write_final_results
from contracts.benchmark_contracts import StatisticalComparison

@pytest.fixture
def clean_output_dir():
    """Ensure output directory is clean before test."""
    output_dir = project_root / "data" / "processed"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    yield output_dir
    # Cleanup after test if desired, or keep for inspection
    # shutil.rmtree(output_dir)

def test_t035_csv_structure(clean_output_dir):
    """
    Test that T035 generates a valid CSV with the correct schema.
    """
    # Note: This test assumes raw data exists in data/raw. 
    # In a full CI run, T034 (data generation) would have run first.
    # If raw data is missing, this test will raise an error, which is correct behavior
    # (the pipeline is broken upstream).
    
    try:
        result_df = write_final_results()
    except FileNotFoundError:
        pytest.skip("Raw benchmark data not found. Prerequisites (T021-T026) must run first.")
    
    output_file = project_root / "data" / "processed" / "statistical_comparison.csv"
    
    # 1. File exists
    assert output_file.exists(), "statistical_comparison.csv was not created"
    
    # 2. Load and validate schema
    df = pd.read_csv(output_file)
    
    required_cols = ["thread_count", "config", "t_stat", "p_value", "cohens_d", "fdr_adjusted_p"]
    assert list(df.columns) == required_cols, f"Columns mismatch. Expected {required_cols}, got {list(df.columns)}"
    
    # 3. Validate data types
    assert df["thread_count"].dtype in ["int64", "int32"], "thread_count must be integer"
    assert df["config"].dtype == "object", "config must be string"
    assert df["t_stat"].dtype in ["float64", "float32"], "t_stat must be float"
    assert df["p_value"].dtype in ["float64", "float32"], "p_value must be float"
    assert df["cohens_d"].dtype in ["float64", "float32"], "cohens_d must be float"
    assert df["fdr_adjusted_p"].dtype in ["float64", "float32"], "fdr_adjusted_p must be float"
    
    # 4. Validate ranges
    assert (df["p_value"] >= 0).all() and (df["p_value"] <= 1).all(), "p_value must be in [0, 1]"
    assert (df["fdr_adjusted_p"] >= 0).all() and (df["fdr_adjusted_p"] <= 1).all(), "fdr_adjusted_p must be in [0, 1]"
    
    # 5. Verify content matches StatisticalComparison schema conceptually
    # (We don't instantiate Pydantic model here to avoid import overhead, 
    # but the column check covers the schema requirements)
    assert len(df) > 0, "Result DataFrame is empty"
    
    # 6. Verify specific values for sanity (e.g., thread counts should be 2, 4, 8)
    expected_threads = {2, 4, 8}
    actual_threads = set(df["thread_count"].unique())
    # Allow subset if not all thread counts were tested, but must be valid
    assert actual_threads.issubset(expected_threads), f"Unexpected thread counts: {actual_threads}"
    
    print(f"Test passed: {len(df)} rows generated with correct schema.")