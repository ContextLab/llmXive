"""
Integration test for T013b: 1000-series selection.

This test verifies the end-to-end flow of selecting 1000 series from a 
realistic sampling report, ensuring the output file is created correctly.
"""
import json
import os
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Import the main function
import sys
sys.path.insert(0, 'code')
from select_1000_series import main as select_main

@pytest.fixture
def realistic_sampling_report(tmp_path):
    """Create a realistic sampling report similar to T013a output."""
    # Simulate a stratified sample of 2000 series
    indices = []
    # Add indices with realistic distribution
    for i in range(2000):
        indices.append(i)
    
    report = {
        "sample_indices": indices,
        "distribution_stats": {
            "total_series": 2000,
            "frequency_distribution": {
                "yearly": 666,
                "quarterly": 667,
                "monthly": 667
            },
            "seasonality_distribution": {
                "yes": 1500,
                "no": 500
            },
            "coverage": 0.95
        },
        "sampling_method": "stratified",
        "seed": 42
    }
    
    report_path = tmp_path / "sampling_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f)
    
    return str(report_path)

def test_end_to_end_selection(realistic_sampling_report, tmp_path):
    """Test the full selection process end-to-end."""
    # Set up paths
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Copy the report to expected location
        import shutil
        shutil.copy(realistic_sampling_report, "data/processed/sampling_report.json")
        
        # Run the selection script
        select_main()
        
        # Verify output file exists
        output_path = "data/processed/sample_indices_1000.csv"
        assert os.path.exists(output_path), f"Output file {output_path} was not created"
        
        # Verify content
        df = pd.read_csv(output_path)
        
        assert len(df) == 1000, f"Expected 1000 rows, got {len(df)}"
        assert "series_id" in df.columns, "Missing 'series_id' column"
        assert df["series_id"].is_monotonic_increasing, "Indices should be sorted"
        assert df["series_id"].is_unique, "Indices should be unique"
        
        # Verify values are in expected range (0 to 1999)
        assert df["series_id"].min() >= 0
        assert df["series_id"].max() < 2000
        
    finally:
        os.chdir(original_cwd)

def test_selection_with_boundary_case(tmp_path):
    """Test selection when exactly 1000 series are available."""
    report = {
        "sample_indices": list(range(1000)),
        "distribution_stats": {
            "total_series": 1000,
            "frequency_distribution": {"yearly": 333, "quarterly": 334, "monthly": 333}
        }
    }
    
    report_path = tmp_path / "sampling_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f)
    
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Copy report
        import shutil
        shutil.copy(report_path, "data/processed/sampling_report.json")
        
        # Run selection
        select_main()
        
        # Verify
        output_path = "data/processed/sample_indices_1000.csv"
        df = pd.read_csv(output_path)
        
        assert len(df) == 1000
        assert list(df["series_id"]) == list(range(1000))
        
    finally:
        os.chdir(original_cwd)

def test_selection_fails_with_insufficient_data(tmp_path):
    """Test that selection fails gracefully with insufficient data."""
    report = {
        "sample_indices": list(range(500)),  # Only 500
        "distribution_stats": {}
    }
    
    report_path = tmp_path / "sampling_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f)
    
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        import shutil
        shutil.copy(report_path, "data/processed/sampling_report.json")
        
        # Should raise an error
        with pytest.raises(ValueError) as excinfo:
            select_main()
        
        assert "Insufficient series" in str(excinfo.value)
        
    finally:
        os.chdir(original_cwd)