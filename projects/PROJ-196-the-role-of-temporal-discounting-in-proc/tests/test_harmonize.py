"""
Unit tests for harmonization module.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import json
import os
import tempfile
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))
from data.harmonize import harmonize_datasets, calculate_cronbach_alpha
from data.generate_dgp import generate_synthetic_data

def test_harmonize_datasets_success():
    """Test successful harmonization of valid datasets."""
    n = 50
    seed = 42
    data_dict = generate_synthetic_data(n, seed)
    
    # Mock project root for logging (avoid actual file writes in unit test)
    # We rely on the function returning the dataframe correctly
    # The actual file writes are side effects that we assume work if logic is correct
    
    result = harmonize_datasets(data_dict)
    
    assert isinstance(result, pd.DataFrame)
    assert len(result) == n
    assert "procrastination_score" in result.columns
    assert "wm_accuracy" in result.columns
    assert "discount_rate_k" not in result.columns # Calculated in modeling, not here
    
    # Check that derived columns exist
    expected_cols = ["participant_id", "procrastination_score", "wm_accuracy", "wm_rt", "age", "gender", "education"]
    for col in expected_cols:
        assert col in result.columns

def test_harmonize_datasets_id_mismatch():
    """Test that harmonization fails on high ID mismatch."""
    # Create a mock data dict with mismatch
    df1 = pd.DataFrame({"participant_id": ["P001", "P002", "P003"]})
    df2 = pd.DataFrame({"participant_id": ["P001", "P002"]}) # Missing P003
    df3 = pd.DataFrame({"participant_id": ["P001", "P002", "P003"]})
    df4 = pd.DataFrame({"participant_id": ["P001", "P002", "P003"]})
    
    data_dict = {
        "discounting": df1,
        "procrastination": df2,
        "nback": df3,
        "demographics": df4
    }
    
    # This should raise SystemExit because mismatch is 1/3 > 0.10
    with pytest.raises(SystemExit) as excinfo:
        harmonize_datasets(data_dict)
    assert excinfo.value.code == 1

def test_cronbach_alpha_calculation():
    """Test Cronbach's alpha calculation logic."""
    # Perfect correlation -> alpha = 1.0 (approx)
    data = pd.DataFrame({
        "item1": [1, 2, 3, 4, 5],
        "item2": [1, 2, 3, 4, 5],
        "item3": [1, 2, 3, 4, 5]
    })
    alpha = calculate_cronbach_alpha(data, ["item1", "item2", "item3"])
    assert alpha > 0.95
    
    # No correlation -> low alpha
    data_rand = pd.DataFrame({
        "item1": [1, 2, 3, 4, 5],
        "item2": [5, 1, 4, 2, 3],
        "item3": [3, 5, 1, 4, 2]
    })
    alpha_rand = calculate_cronbach_alpha(data_rand, ["item1", "item2", "item3"])
    assert alpha_rand < 0.5