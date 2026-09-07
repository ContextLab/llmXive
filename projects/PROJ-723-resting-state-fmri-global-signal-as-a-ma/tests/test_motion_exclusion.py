"""
Unit tests for motion exclusion logic in T014.
Verifies that subjects with Mean_FD > 0.5mm are excluded.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion import apply_motion_exclusion

def test_motion_exclusion_basic():
    """Test that subjects with FD > 0.5 are excluded."""
    data = {
        "Subject_ID": ["S1", "S2", "S3", "S4"],
        "Global_Signal_SD": [1.0, 2.0, 1.5, 3.0],
        "MWQ_Score": [10, 20, 15, 25],
        "Mean_FD": [0.1, 0.6, 0.4, 0.8],  # S2 and S4 should be excluded
        "Mean_DVARS": [5.0, 6.0, 4.0, 7.0]
    }
    df = pd.DataFrame(data)
    
    result = apply_motion_exclusion(df, threshold=0.5)
    
    assert len(result) == 2, f"Expected 2 subjects, got {len(result)}"
    assert "S1" in result["Subject_ID"].values
    assert "S3" in result["Subject_ID"].values
    assert "S2" not in result["Subject_ID"].values
    assert "S4" not in result["Subject_ID"].values

def test_motion_exclusion_boundary():
    """Test boundary condition: FD exactly 0.5 should be kept."""
    data = {
        "Subject_ID": ["S1", "S2"],
        "Global_Signal_SD": [1.0, 2.0],
        "MWQ_Score": [10, 20],
        "Mean_FD": [0.5, 0.5001],  # S1 kept, S2 excluded
        "Mean_DVARS": [5.0, 6.0]
    }
    df = pd.DataFrame(data)
    
    result = apply_motion_exclusion(df, threshold=0.5)
    
    assert len(result) == 1
    assert result["Subject_ID"].iloc[0] == "S1"

def test_motion_exclusion_all_kept():
    """Test case where all subjects have FD <= 0.5."""
    data = {
        "Subject_ID": ["S1", "S2"],
        "Global_Signal_SD": [1.0, 2.0],
        "MWQ_Score": [10, 20],
        "Mean_FD": [0.1, 0.4],
        "Mean_DVARS": [5.0, 6.0]
    }
    df = pd.DataFrame(data)
    
    result = apply_motion_exclusion(df, threshold=0.5)
    
    assert len(result) == 2

def test_motion_exclusion_all_excluded():
    """Test case where all subjects have FD > 0.5."""
    data = {
        "Subject_ID": ["S1", "S2"],
        "Global_Signal_SD": [1.0, 2.0],
        "MWQ_Score": [10, 20],
        "Mean_FD": [0.6, 0.9],
        "Mean_DVARS": [5.0, 6.0]
    }
    df = pd.DataFrame(data)
    
    result = apply_motion_exclusion(df, threshold=0.5)
    
    assert len(result) == 0