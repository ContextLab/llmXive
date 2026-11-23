"""
Integration test for Task T039: Output correlation results.

This test verifies that the output script correctly generates
`data/processed/correlation_results.csv` with the required columns
and valid data types.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis.output_correlation_results import (
    load_correlation_data,
    load_stability_data,
    merge_and_format_results,
    write_results,
    process_correlation_output
)

# Sample test data
SAMPLE_CORRELATION_DATA = {
    "connection_id": ["conn_001", "conn_002", "conn_003"],
    "r_value": [0.45, -0.23, 0.78],
    "p_value": [0.001, 0.045, 0.0001],
    "effect_size": [0.45, 0.23, 0.78],
    "ci_lower": [0.10, -0.45, 0.50],
    "ci_upper": [0.80, 0.01, 0.95]
}

SAMPLE_STABILITY_DATA = {
    "connection_id": ["conn_001", "conn_002", "conn_003"],
    "stability_flag": ["high", "low", "high"]
}

@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for input and output files."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Write sample input files
    corr_path = data_dir / "correlation_analysis_intermediate.csv"
    pd.DataFrame(SAMPLE_CORRELATION_DATA).to_csv(corr_path, index=False)
    
    stab_path = data_dir / "sensitivity_analysis.csv"
    pd.DataFrame(SAMPLE_STABILITY_DATA).to_csv(stab_path, index=False)
    
    output_path = data_dir / "correlation_results.csv"
    
    return {
        "correlation_input": corr_path,
        "stability_input": stab_path,
        "output": output_path,
        "temp_dir": tmp_path
    }

def test_load_correlation_data(temp_dirs):
    """Test loading correlation data from CSV."""
    df = load_correlation_data(temp_dirs["correlation_input"])
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert "connection_id" in df.columns
    assert "r_value" in df.columns
    assert "p_value" in df.columns

def test_load_stability_data(temp_dirs):
    """Test loading stability data from CSV."""
    df = load_stability_data(temp_dirs["stability_input"])
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert "connection_id" in df.columns
    assert "stability_flag" in df.columns

def test_merge_and_format_results(temp_dirs):
    """Test merging and formatting logic."""
    corr_df = load_correlation_data(temp_dirs["correlation_input"])
    stab_df = load_stability_data(temp_dirs["stability_input"])
    
    merged = merge_and_format_results(corr_df, stab_df)
    
    # Check required output columns
    required_cols = [
        "connection_id", "r_value", "p_value", 
        "effect_size", "ci_95", "stability_flag"
    ]
    for col in required_cols:
        assert col in merged.columns, f"Missing column: {col}"
    
    # Check ci_95 format
    assert merged["ci_95"].iloc[0].startswith("[")
    assert merged["ci_95"].iloc[0].endswith("]")

def test_write_results(temp_dirs):
    """Test writing results to CSV."""
    corr_df = load_correlation_data(temp_dirs["correlation_input"])
    stab_df = load_stability_data(temp_dirs["stability_input"])
    merged = merge_and_format_results(corr_df, stab_df)
    
    output_path = write_results(merged, temp_dirs["output"])
    
    assert output_path.exists()
    
    # Verify written content
    written_df = pd.read_csv(output_path)
    assert len(written_df) == 3
    assert "stability_flag" in written_df.columns

def test_full_pipeline(temp_dirs):
    """Test the full pipeline from input to output."""
    output_path = process_correlation_output(
        correlation_input=temp_dirs["correlation_input"],
        stability_input=temp_dirs["stability_input"],
        output=temp_dirs["output"]
    )
    
    # Verify file exists
    assert output_path.exists(), "Output file was not created"
    
    # Verify content matches requirements
    df = pd.read_csv(output_path)
    
    # Check exact columns required by T039
    expected_columns = [
        "connection_id",
        "r_value",
        "p_value",
        "effect_size",
        "ci_95",
        "stability_flag"
    ]
    
    for col in expected_columns:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Verify data types and basic validity
    assert len(df) == 3
    assert all(df["stability_flag"].isin(["high", "low", "unknown"]))
    
    # Verify numeric columns are numeric
    assert pd.api.types.is_float_dtype(df["r_value"])
    assert pd.api.types.is_float_dtype(df["p_value"])
    assert pd.api.types.is_float_dtype(df["effect_size"])

def test_missing_input_file_raises_error(tmp_path):
    """Test that missing input files raise appropriate errors."""
    nonexistent_path = tmp_path / "nonexistent.csv"
    
    with pytest.raises(FileNotFoundError):
        load_correlation_data(nonexistent_path)
    
    with pytest.raises(FileNotFoundError):
        load_stability_data(nonexistent_path)

def test_missing_columns_raises_error(tmp_path):
    """Test that missing required columns raise errors."""
    incomplete_data = tmp_path / "incomplete.csv"
    pd.DataFrame({"connection_id": ["conn_001"]}).to_csv(incomplete_data, index=False)
    
    with pytest.raises(ValueError):
        load_correlation_data(incomplete_data)