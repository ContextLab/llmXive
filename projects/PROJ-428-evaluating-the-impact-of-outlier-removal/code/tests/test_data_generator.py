import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_generator import (
    generate_normal_distribution,
    generate_lognormal_distribution,
    generate_exponential_distribution,
    generate_beta_distribution,
    generate_gamma_distribution,
    save_ground_truth_params
)

class TestDataGenerator:
    """Tests for the synthetic data generation functions."""

    def test_generate_normal_distribution(self):
        """Test Normal distribution generation."""
        n_samples = 1000
        mean = 10.0
        std = 2.0
        
        df, params = generate_normal_distribution(n_samples, mean, std, seed=42)
        
        # Check DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert 'value' in df.columns
        assert len(df) == n_samples
        
        # Check params
        assert params['distribution'] == 'normal'
        assert params['mean'] == mean
        assert params['std'] == std
        assert params['n_samples'] == n_samples
        assert abs(params['variance'] - std**2) < 1e-10

    def test_generate_lognormal_distribution(self):
        """Test LogNormal distribution generation."""
        n_samples = 1000
        mu = 2.0
        sigma = 0.5
        
        df, params = generate_lognormal_distribution(n_samples, mu, sigma, seed=42)
        
        # Check DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert 'value' in df.columns
        assert len(df) == n_samples
        
        # Check all values are positive (property of lognormal)
        assert all(df['value'] > 0)
        
        # Check params
        assert params['distribution'] == 'lognormal'
        assert params['mu'] == mu
        assert params['sigma'] == sigma
        assert params['n_samples'] == n_samples
        assert 'theoretical_variance' in params

    def test_generate_exponential_distribution(self):
        """Test Exponential distribution generation."""
        n_samples = 1000
        scale = 1.0
        
        df, params = generate_exponential_distribution(n_samples, scale, seed=42)
        
        # Check DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert 'value' in df.columns
        assert len(df) == n_samples
        
        # Check all values are non-negative (property of exponential)
        assert all(df['value'] >= 0)
        
        # Check params
        assert params['distribution'] == 'exponential'
        assert params['scale'] == scale
        assert params['n_samples'] == n_samples
        assert abs(params['theoretical_variance'] - scale**2) < 1e-10

    def test_generate_beta_distribution(self):
        """Test Beta distribution generation."""
        n_samples = 1000
        alpha = 2.0
        beta = 5.0
        
        df, params = generate_beta_distribution(n_samples, alpha, beta, seed=42)
        
        # Check DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert 'value' in df.columns
        assert len(df) == n_samples
        
        # Check all values are in [0, 1] (property of beta)
        assert all((df['value'] >= 0) & (df['value'] <= 1))
        
        # Check params
        assert params['distribution'] == 'beta'
        assert params['alpha'] == alpha
        assert params['beta'] == beta
        assert params['n_samples'] == n_samples
        assert 'theoretical_variance' in params

    def test_generate_gamma_distribution(self):
        """Test Gamma distribution generation."""
        n_samples = 1000
        shape = 3.0
        scale = 2.0
        
        df, params = generate_gamma_distribution(n_samples, shape, scale, seed=42)
        
        # Check DataFrame structure
        assert isinstance(df, pd.DataFrame)
        assert 'value' in df.columns
        assert len(df) == n_samples
        
        # Check all values are non-negative (property of gamma)
        assert all(df['value'] >= 0)
        
        # Check params
        assert params['distribution'] == 'gamma'
        assert params['shape'] == shape
        assert params['scale'] == scale
        assert params['n_samples'] == n_samples
        assert abs(params['theoretical_variance'] - shape * scale**2) < 1e-10

    def test_save_ground_truth_params(self, tmp_path):
        """Test saving ground truth parameters to JSON."""
        params_list = [
            {'distribution': 'normal', 'mean': 10.0, 'std': 2.0},
            {'distribution': 'exponential', 'scale': 1.0}
        ]
        
        output_path = tmp_path / "test_params.json"
        save_ground_truth_params(params_list, output_path)
        
        # Check file exists
        assert output_path.exists()
        
        # Check content
        with open(output_path, 'r') as f:
            loaded_params = json.load(f)
        
        assert len(loaded_params) == len(params_list)
        assert loaded_params[0]['distribution'] == 'normal'
        assert loaded_params[1]['distribution'] == 'exponential'

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        n_samples = 100
        mean = 5.0
        std = 1.0
        seed = 123
        
        df1, _ = generate_normal_distribution(n_samples, mean, std, seed=seed)
        df2, _ = generate_normal_distribution(n_samples, mean, std, seed=seed)
        
        # Check that the generated values are identical
        assert df1.equals(df2)
        
        # Check that different seed produces different results
        df3, _ = generate_normal_distribution(n_samples, mean, std, seed=seed+1)
        assert not df1.equals(df3)