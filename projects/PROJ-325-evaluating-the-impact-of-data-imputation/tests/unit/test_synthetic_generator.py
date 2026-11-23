import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.synthetic import generate_synthetic_data, validate_schema

class TestSyntheticGenerator:
    def test_generate_mcar_data(self):
        """Test generation of MCAR synthetic data."""
        df = generate_synthetic_data(n=100, true_mean=50, true_variance=100, 
                                     missing_rate=0.2, mechanism='MCAR', seed=42)
        
        assert len(df) == 100
        assert 'value' in df.columns
        assert df['missingness_mechanism'].iloc[0] == 'MCAR'
        assert df['true_mean'].iloc[0] == 50
        assert df['true_variance'].iloc[0] == 100
        
        # Check missing rate is approximately 0.2
        missing_rate = df['value'].isna().mean()
        assert 0.1 <= missing_rate <= 0.3, f"Missing rate {missing_rate} not in expected range"

    def test_generate_mar_data(self):
        """Test generation of MAR synthetic data."""
        df = generate_synthetic_data(n=100, true_mean=50, true_variance=100, 
                                     missing_rate=0.2, mechanism='MAR', seed=42)
        
        assert len(df) == 100
        assert 'value' in df.columns
        assert df['missingness_mechanism'].iloc[0] == 'MAR'

    def test_schema_validation(self):
        """Test schema validation logic."""
        valid_metadata = {
            'true_mean': 50.0,
            'true_variance': 100.0,
            'missingness_mechanism': 'MAR',
            'n': 1000,
            'missing_rate': 0.2
        }
        
        assert validate_schema(valid_metadata, "") is True
        
        invalid_metadata = valid_metadata.copy()
        invalid_metadata['missingness_mechanism'] = 'MNAR'
        assert validate_schema(invalid_metadata, "") is False

    def test_seed_reproducibility(self):
        """Test that same seed produces same results."""
        df1 = generate_synthetic_data(n=50, true_mean=50, true_variance=100, 
                                      missing_rate=0.2, mechanism='MCAR', seed=123)
        df2 = generate_synthetic_data(n=50, true_mean=50, true_variance=100, 
                                      missing_rate=0.2, mechanism='MCAR', seed=123)
        
        pd.testing.assert_frame_equal(df1, df2)