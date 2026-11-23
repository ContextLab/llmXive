"""
Unit tests for DGP generation module.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from data.generate_dgp import generate_synthetic_data, validate_dgp_config, DGP_PARAMS

def test_dgp_params_valid():
    """Test that default DGP parameters are valid."""
    # Should not raise
    validate_dgp_config(DGP_PARAMS)
    assert DGP_PARAMS["k_mean"] > 0
    assert sum(DGP_PARAMS["gender_distribution"].values()) == 1.0

def test_generate_synthetic_data_structure():
    """Test that generate_synthetic_data returns correct structure."""
    n = 10
    seed = 42
    result = generate_synthetic_data(n, seed)
    
    assert isinstance(result, dict)
    assert set(result.keys()) == {"discounting", "procrastination", "nback", "demographics"}
    
    for key, df in result.items():
        assert isinstance(df, pd.DataFrame)
        assert len(df) == n
        assert "participant_id" in df.columns

def test_generate_synthetic_data_values():
    """Test that generated data has reasonable values."""
    n = 50
    seed = 123
    result = generate_synthetic_data(n, seed)
    
    # Check procrastination items
    proc_df = result["procrastination"]
    for i in range(1, 11):
        col = f"procrastination_item_{i}"
        assert col in proc_df.columns
        assert proc_df[col].between(1, 5).all()
        
    # Check nback
    nback_df = result["nback"]
    assert nback_df["wm_accuracy"].between(0.5, 0.99).all()
    assert nback_df["wm_rt"].between(200, 1000).all()
    
    # Check demographics
    demo_df = result["demographics"]
    assert demo_df["age"].between(18, 80).all()
    assert set(demo_df["gender"]).issubset({"male", "female", "other"})
