"""
Integration test for outlier detection and reporting (T048).
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent to path for imports if running standalone
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingest import detect_outliers_iqr, save_outlier_report, filter_outliers

def test_outlier_detection_basic():
    """Test that outliers are correctly identified using IQR."""
    # Create a dataset with known outliers
    data = {
        "value": [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]  # 100 is a clear outlier
    }
    df = pd.DataFrame(data)
    
    # Run detection
    report = detect_outliers_iqr(df, ["value"])
    
    assert report["total_outlier_count"] == 1, f"Expected 1 outlier, got {report['total_outlier_count']}"
    assert 9 in report["outlier_indices"], f"Expected index 9 to be flagged as outlier"
    assert "value" in report["per_column_details"]
    assert report["per_column_details"]["value"]["count"] == 1

def test_outlier_report_generation(tmp_path):
    """Test that outlier report is saved correctly."""
    data = {
        "taxon_A": [10, 12, 11, 13, 1000],
        "sleep_hours": [7.0, 7.2, 6.8, 7.1, 2.0]
    }
    df = pd.DataFrame(data)
    
    report = detect_outliers_iqr(df, ["taxon_A", "sleep_hours"])
    output_path = tmp_path / "outlier_report.json"
    
    save_outlier_report(report, output_path)
    
    assert output_path.exists(), "Outlier report file not created"
    
    with open(output_path, 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report["total_outlier_count"] > 0, "Expected outliers to be detected"
    assert "per_column_details" in saved_report

def test_high_outlier_density_flag():
    """Test that high outlier density is flagged correctly."""
    # Create a dataset where >10% are outliers
    # 20 rows, 3 outliers = 15%
    data = {
        "value": list(range(17)) + [100, 101, 102]
    }
    df = pd.DataFrame(data)
    
    report = detect_outliers_iqr(df, ["value"])
    
    total_rows = len(df)
    excluded_count = report["total_outlier_count"]
    ratio = excluded_count / total_rows
    
    # 3/20 = 0.15 which is >= 0.10 threshold
    assert ratio >= 0.10, "Test setup failed: ratio should be >= 0.10"
    
    # Logic check: The main load_data function adds the flag, 
    # but we verify the calculation here.
    assert excluded_count >= 3, "Expected at least 3 outliers"

def test_filter_outliers():
    """Test that filtering removes the correct rows."""
    data = {
        "id": [1, 2, 3, 4, 5],
        "value": [10, 20, 30, 40, 500]
    }
    df = pd.DataFrame(data)
    
    indices_to_remove = [4] # Index of 500
    filtered_df = filter_outliers(df, indices_to_remove)
    
    assert len(filtered_df) == 4, "Expected 4 rows after filtering"
    assert 500 not in filtered_df["value"].values, "Outlier value should be removed"
    assert 4 not in filtered_df.index.values, "Index 4 should be removed"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
