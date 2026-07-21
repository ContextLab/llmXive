import pytest
import os
import sys
import json
import csv
import tempfile
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from code_06_bin_complexity import (
    calculate_tertiles,
    assign_bin,
    bin_complexity_metrics,
    update_metadata
)

def test_calculate_tertiles_simple():
    """Test tertile calculation on a known small dataset."""
    # 10 items: indices 0-9. 33% -> idx 3, 66% -> idx 6.
    # Sorted: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    # Lower boundary = value at idx 3 = 3
    # Upper boundary = value at idx 6 = 6
    values = list(range(10))
    lower, upper = calculate_tertiles(values)
    assert lower == 3
    assert upper == 6

def test_assign_bin_logic():
    """Test bin assignment logic."""
    # Boundaries: Low <= 5, Medium (5, 10], High > 10
    assert assign_bin(0, 5, 10) == "Low"
    assert assign_bin(5, 5, 10) == "Low"
    assert assign_bin(6, 5, 10) == "Medium"
    assert assign_bin(10, 5, 10) == "Medium"
    assert assign_bin(11, 5, 10) == "High"

def test_bin_complexity_metrics_integration():
    """Test the full binning workflow on mock data."""
    mock_data = [
        {"cc": 2.0, "halstead_volume": 10.0},
        {"cc": 5.0, "halstead_volume": 20.0},
        {"cc": 8.0, "halstead_volume": 30.0},
        {"cc": 12.0, "halstead_volume": 40.0},
    ]
    
    # Sort values for cc: [2, 5, 8, 12]. n=4. idx1=1 (val 5), idx2=2 (val 8).
    # Lower=5, Upper=8.
    # Bins: 2->Low, 5->Low, 8->Medium, 12->High
    
    result_data, lower, upper = bin_complexity_metrics(mock_data, "cc")
    
    assert lower == 5.0
    assert upper == 8.0
    assert result_data[0]["cc_bin"] == "Low"
    assert result_data[1]["cc_bin"] == "Low"
    assert result_data[2]["cc_bin"] == "Medium"
    assert result_data[3]["cc_bin"] == "High"

def test_update_metadata_creates_file():
    """Test that update_metadata creates the file with correct structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        meta_path = os.path.join(tmpdir, "metadata.json")
        boundaries = {"cc": {"low_max": 1.0, "medium_max": 2.0}}
        
        update_metadata(meta_path, boundaries)
        
        assert os.path.exists(meta_path)
        with open(meta_path, 'r') as f:
            data = json.load(f)
        
        assert "binning_boundaries" in data
        assert data["binning_boundaries"]["cc"]["low_max"] == 1.0
        assert data["binning_status"] == "completed"
