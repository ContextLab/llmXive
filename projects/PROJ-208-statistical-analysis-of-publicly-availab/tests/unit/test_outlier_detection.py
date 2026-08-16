import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.outlier_detection import detect_outliers_iqr, save_report

def test_iqr_calculation():
    """Test that IQR outlier detection works correctly."""
    # Create a dataset with known outliers
    # Q1=10, Q3=20, IQR=10. Upper bound = 20 + 15 = 35.
    # Values: 5, 10, 15, 20, 25, 30, 35, 40 (40 is outlier)
    data = {
        "issue_id": range(8),
        "resolution_time_hours": [5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0]
    }
    df = pd.DataFrame(data)
    
    flagged_df, stats = detect_outliers_iqr(df, "resolution_time_hours")
    
    # Verify statistics
    assert abs(stats["q1"] - 10.0) < 0.1
    assert abs(stats["q3"] - 20.0) < 0.1
    assert abs(stats["iqr"] - 10.0) < 0.1
    assert abs(stats["upper_bound"] - 35.0) < 0.1
    
    # Verify outlier count
    assert stats["outlier_count"] == 1
    assert stats["outlier_percentage"] == (1/8) * 100
    
    # Verify the correct row is flagged
    assert flagged_df.iloc[7]["is_outlier"] == True
    for i in range(7):
        assert flagged_df.iloc[i]["is_outlier"] == False

def test_save_report_format():
    """Test that the report is saved in the correct JSON format."""
    import tempfile
    
    data = {
        "issue_id": [1, 2, 3],
        "resolution_time_hours": [10.0, 20.0, 100.0] # 100 is likely an outlier
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_outlier_report.json"
        
        # Run detection
        flagged_df, stats = detect_outliers_iqr(df, "resolution_time_hours")
        save_report(stats, flagged_df, output_path)
        
        # Verify file exists
        assert output_path.exists()
        
        # Verify JSON structure
        with open(output_path) as f:
            report = json.load(f)
        
        assert "method" in report
        assert "statistics" in report
        assert "outliers" in report
        
        assert report["statistics"]["outlier_count"] >= 0
        assert report["statistics"]["total_count"] == 3
        assert "outlier_percentage" in report["statistics"]