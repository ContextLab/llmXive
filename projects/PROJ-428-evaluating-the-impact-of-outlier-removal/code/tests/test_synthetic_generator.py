import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import json
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from synthetic_generator import (
    generate_normal_distribution,
    generate_lognormal_distribution,
    generate_exponential_distribution,
    generate_beta_distribution,
    generate_gamma_distribution,
    save_ground_truth_params
)

class TestSyntheticGenerator:
    
    def test_normal_distribution_mean_variance(self):
        """Test that Normal distribution has approximately correct mean and variance."""
        np.random.seed(42)
        df, params = generate_normal_distribution(10000, (0, 10), (1, 5))
        
        assert 'value' in df.columns
        assert len(df) == 10000
        
        # Check that the generated parameters match the saved params
        assert abs(df['value'].mean() - params['mean']) < 0.5  # Allow some sampling error
        assert abs(df['value'].var() - params['variance']) < 0.5
        
        # Check theoretical variance is positive
        assert params['variance'] > 0

    def test_lognormal_distribution_variance(self):
        """Test LogNormal variance calculation."""
        np.random.seed(42)
        df, params = generate_lognormal_distribution(10000, (0, 1), (0.5, 1.5))
        
        assert 'value' in df.columns
        assert len(df) == 10000
        assert params['variance'] > 0

    def test_exponential_distribution_variance(self):
        """Test Exponential variance calculation."""
        np.random.seed(42)
        df, params = generate_exponential_distribution(10000, (1, 3))
        
        assert 'value' in df.columns
        assert len(df) == 10000
        
        # Variance = scale^2
        expected_var = params['scale'] ** 2
        assert abs(params['variance'] - expected_var) < 1e-6

    def test_beta_distribution_variance(self):
        """Test Beta variance calculation."""
        np.random.seed(42)
        df, params = generate_beta_distribution(10000, (2, 5), (2, 5))
        
        assert 'value' in df.columns
        assert len(df) == 10000
        
        # Beta values should be in [0, 1]
        assert df['value'].min() >= 0
        assert df['value'].max() <= 1
        assert params['variance'] > 0

    def test_gamma_distribution_variance(self):
        """Test Gamma variance calculation."""
        np.random.seed(42)
        df, params = generate_gamma_distribution(10000, (2, 5), (0.5, 2.0))
        
        assert 'value' in df.columns
        assert len(df) == 10000
        
        # Gamma values should be positive
        assert df['value'].min() >= 0
        assert params['variance'] > 0

    def test_save_ground_truth_params(self, tmp_path):
        """Test saving ground truth parameters to JSON."""
        params = {
            'Normal': {'distribution': 'Normal', 'variance': 2.5},
            'Exponential': {'distribution': 'Exponential', 'variance': 4.0}
        }
        
        output_path = tmp_path / "test_params.json"
        save_ground_truth_params(params, output_path)
        
        assert output_path.exists()
        
        with open(output_path) as f:
            loaded = json.load(f)
        
        assert 'Normal' in loaded
        assert 'Exponential' in loaded
        assert loaded['Normal']['variance'] == 2.5