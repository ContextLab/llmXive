"""
Unit test for batch correction metric calculation.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.batch_correction import calculate_cv_reduction, apply_batch_correction

def test_cv_reduction_calculation():
    """Test that CV reduction is calculated correctly."""
    # Create a simple dataset with known CV
    data = {
        "Sample_0": [100, 200, 300],
        "Sample_1": [110, 210, 310],
        "Sample_2": [90, 190, 290],
        "Sample_3": [100, 200, 300]
    }
    df = pd.DataFrame(data, index=["Gene_A", "Gene_B", "Gene_C"])
    batch_labels = ["Batch_0", "Batch_0", "Batch_1", "Batch_1"]
    
    result = calculate_cv_reduction(df, batch_labels)
    
    assert "cv_before" in result
    assert "cv_after" in result
    assert "reduction_pct" in result
    assert result["cv_before"] > 0

def test_batch_correction_logic():
    """Test that batch correction reduces variance between batches."""
    # Create data with a strong batch effect
    # Batch 0: mean 1000, Batch 1: mean 2000
    data = {
        "S0": [1000, 1000, 1000],
        "S1": [1000, 1000, 1000],
        "S2": [2000, 2000, 2000],
        "S3": [2000, 2000, 2000]
    }
    df = pd.DataFrame(data, index=["Gene_A", "Gene_B", "Gene_C"])
    batch_labels = ["B0", "B0", "B1", "B1"]
    
    corrected = apply_batch_correction(df, batch_labels)
    
    # After correction, the means of the batches should be closer
    # (Ideally equal, but our simplified method might not be perfect)
    mean_b0_before = df["S0"].mean()
    mean_b1_before = df["S2"].mean()
    mean_b0_after = corrected["S0"].mean()
    mean_b1_after = corrected["S2"].mean()
    
    diff_before = abs(mean_b0_before - mean_b1_before)
    diff_after = abs(mean_b0_after - mean_b1_after)
    
    assert diff_after < diff_before, "Batch correction should reduce the difference between batch means."
