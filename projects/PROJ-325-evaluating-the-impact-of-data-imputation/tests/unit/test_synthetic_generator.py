"""
Unit tests for code/synthetic_generator.py
"""
import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from synthetic_generator import generate_synthetic_data, validate_schema

class TestSyntheticGenerator:
    
    def test_generate_mcar_structure(self):
        """Test that MCAR generation produces expected structure."""
        df, meta = generate_synthetic_data(n_samples=100, missingness_mechanism="MCAR", seed=42)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 100
        assert 'id' in df.columns
        assert 'covariate_X' in df.columns
        assert 'target_Y' in df.columns
        assert meta['missingness_mechanism'] == "MCAR"
        assert meta['n_samples'] == 100

    def test_generate_mar_structure(self):
        """Test that MAR generation produces expected structure."""
        df, meta = generate_synthetic_data(n_samples=100, missingness_mechanism="MAR", seed=42)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 100
        assert meta['missingness_mechanism'] == "MAR"

    def test_missingness_rate_approximation(self):
        """Test that missingness rate is approximately correct."""
        n = 5000
        target_rate = 0.20
        df, _ = generate_synthetic_data(n_samples=n, missing_rate=target_rate, seed=123)
        
        observed_rate = df['target_Y'].isna().sum() / n
        # Allow 5% tolerance for randomness
        assert abs(observed_rate - target_rate) < 0.05

    def test_known_mean_variance(self):
        """Test that generated data approximates true mean and variance (ignoring missing)."""
        true_mean = 100.0
        true_var = 25.0
        n = 100000 # Large sample for convergence
        
        df, meta = generate_synthetic_data(
            n_samples=n, 
            true_mean=true_mean, 
            true_variance=true_var, 
            missingness_mechanism="MCAR", # MCAR ensures observed mean is unbiased
            seed=999
        )
        
        # Calculate mean of non-missing values
        observed_mean = df['target_Y'].mean()
        observed_var = df['target_Y'].var()
        
        # Tolerance for Monte Carlo error
        assert abs(observed_mean - true_mean) < 0.5
        assert abs(observed_var - true_var) < 1.0

    def test_metadata_content(self):
        """Test that metadata contains required fields."""
        df, meta = generate_synthetic_data()
        
        assert 'true_mean' in meta
        assert 'true_variance' in meta
        assert 'missingness_mechanism' in meta
        assert 'seed' in meta
        assert isinstance(meta['true_mean'], float)
        assert isinstance(meta['true_variance'], float)

    def test_invalid_missing_rate(self):
        """Test that invalid missing rate raises error."""
        with pytest.raises(ValueError):
            generate_synthetic_data(missing_rate=1.5)
        
        with pytest.raises(ValueError):
            generate_synthetic_data(missing_rate=-0.1)

    def test_invalid_mechanism(self):
        """Test that invalid mechanism raises error."""
        with pytest.raises(ValueError):
            generate_synthetic_data(missingness_mechanism="MNAR")
