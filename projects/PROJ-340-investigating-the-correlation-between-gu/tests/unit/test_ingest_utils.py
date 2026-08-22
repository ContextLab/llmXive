"""
Unit tests for data ingestion utilities.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.ingest import detect_outliers_iqr, filter_outliers

def test_detect_outliers_iqr():
    """Test IQR outlier detection logic."""
    # Create a dataset with known outliers
    data = pd.DataFrame({
        "value": [10, 12, 11, 13, 12, 100, 11, 12, 13, 11],
        "id": list(range(10))
    })
    
    outliers = detect_outliers_iqr(data, "value")
    
    assert len(outliers) == 1, "Should detect exactly one outlier"
    assert outliers.iloc[0]["id"] == 5, "Outlier should be at index 5"
    assert outliers.iloc[0]["value"] == 100, "Outlier value should be 100"

def test_filter_outliers():
    """Test outlier filtering removes detected points."""
    data = pd.DataFrame({
        "value": [10, 12, 11, 13, 12, 100, 11, 12, 13, 11],
        "id": list(range(10))
    })
    
    filtered_data, report = filter_outliers(data, "value")
    
    assert len(filtered_data) == 9, "Should remove exactly one row"
    assert 100 not in filtered_data["value"].values, "Outlier value should be removed"
    assert report["exclusion_count"] == 1, "Report should reflect one exclusion"
