import os
import json
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path if needed
sys_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if sys_path not in os.sys.path:
    os.sys.path.insert(0, sys_path)

from code.data.synthetic import generate_synthetic_data_mcar, validate_schema

def test_generate_mcar():
    """Test that MCAR generator produces data with correct properties."""
    n = 1000
    true_mean = 50.0
    true_variance = 100.0
    missing_rate = 0.2
    seed = 42
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "test_mcar.csv")
        meta_path = os.path.join(tmpdir, "test_mcar_meta.json")
        
        df = generate_synthetic_data_mcar(
            n=n,
            true_mean=true_mean,
            true_variance=true_variance,
            missing_rate=missing_rate,
            seed=seed,
            output_csv=csv_path,
            output_meta=meta_path
        )
        
        # Check file existence
        assert os.path.exists(csv_path)
        assert os.path.exists(meta_path)
        
        # Check data shape
        assert len(df) == n
        assert "value" in df.columns
        assert "value_masked" in df.columns
        assert "is_missing" in df.columns
        
        # Check missing rate (approximate due to randomness)
        observed_missing_rate = df["is_missing"].mean()
        assert abs(observed_missing_rate - missing_rate) < 0.05
        
        # Check metadata
        with open(meta_path, "r") as f:
            meta = json.load(f)
        
        assert meta["true_mean"] == true_mean
        assert meta["true_variance"] == true_variance
        assert meta["missingness_mechanism"] == "MCAR"
        assert meta["n"] == n
        assert meta["missing_rate"] == missing_rate
        
        # Validate schema
        assert validate_schema(meta)

def test_mcar_independence():
    """Test that MCAR missingness is independent of data values."""
    n = 10000
    true_mean = 50.0
    true_variance = 100.0
    missing_rate = 0.2
    seed = 123
    
    df = generate_synthetic_data_mcar(
        n=n,
        true_mean=true_mean,
        true_variance=true_variance,
        missing_rate=missing_rate,
        seed=seed
    )
    
    # Split by missing status
    missing_vals = df.loc[df["is_missing"] == True, "value"]
    observed_vals = df.loc[df["is_missing"] == False, "value"]
    
    # Perform t-test to check if means are significantly different
    # For MCAR, they should be similar (though small differences expected)
    t_stat, p_val = scipy.stats.ttest_ind(missing_vals, observed_vals)
    
    # With MCAR, we don't expect a systematic difference
    # We allow some tolerance due to random sampling
    # A p-value > 0.01 suggests no significant difference
    # Note: This is a statistical check, not a strict equality check
    assert p_val > 0.01, "MCAR missingness should be independent of values"

def test_schema_validation():
    """Test that metadata conforms to schema."""
    meta = {
        "true_mean": 50.0,
        "true_variance": 100.0,
        "missingness_mechanism": "MCAR",
        "n": 1000,
        "missing_rate": 0.2
    }
    assert validate_schema(meta)
    
    # Test invalid schema
    invalid_meta = meta.copy()
    invalid_meta["missingness_mechanism"] = "MNAR"
    assert not validate_schema(invalid_meta)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
