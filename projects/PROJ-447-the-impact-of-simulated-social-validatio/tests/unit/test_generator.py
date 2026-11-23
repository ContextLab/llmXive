"""
Unit tests for code/data/generator.py

Tests focus on:
1. SEM model structure definition
2. Synthetic data generation process
3. Psychometric validation (Cronbach's Alpha)
4. Association recovery verification
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from data.generator import (
    generate_synthetic_data,
    validate_rses_psychometrics,
    _calculate_cronbach_alpha,
    _generate_rses_items,
    _generate_latent_factors,
    verify_association_recovery
)
from utils.exceptions import InsufficientSampleError
from utils.constants import get_seed

class TestLatentFactorGeneration:
    def test_latent_factors_shape(self):
        """Test that latent factors are generated with correct shape."""
        n = 100
        df = _generate_latent_factors(n, seed=42)
        assert len(df) == n
        expected_cols = ['latent_self_esteem', 'latent_social_validation', 
                       'latent_offline_relationships', 'latent_intrinsic_traits']
        assert list(df.columns) == expected_cols

    def test_latent_factors_distribution(self):
        """Test that latent factors have reasonable distributions."""
        n = 1000
        df = _generate_latent_factors(n, seed=42)
        # Should be roughly standardized (mean ~0, std ~1)
        for col in df.columns:
            assert 0.8 < df[col].std() < 1.2
            assert -0.5 < df[col].mean() < 0.5

class TestRSESItemGeneration:
    def test_rses_items_shape(self):
        """Test that RSES items are generated correctly."""
        n = 100
        latent = np.random.normal(0, 1, n)
        items_df = _generate_rses_items(latent, seed=42)
        
        assert len(items_df) == n
        expected_cols = [f'q{i}' for i in range(1, 11)]
        assert list(items_df.columns) == expected_cols

    def test_rses_items_range(self):
        """Test that RSES items are within the 1-4 Likert scale."""
        n = 100
        latent = np.random.normal(0, 1, n)
        items_df = _generate_rses_items(latent, seed=42)
        
        for col in items_df.columns:
            assert items_df[col].min() >= 1.0
            assert items_df[col].max() <= 4.0

class TestCronbachAlpha:
    def test_cronbach_alpha_calculation(self):
        """Test the Cronbach's alpha calculation function."""
        # Create a perfectly correlated dataset -> alpha should be 1.0
        n = 100
        data = pd.DataFrame({
            'q1': [1.0] * n,
            'q2': [1.0] * n,
            'q3': [1.0] * n
        })
        alpha = _calculate_cronbach_alpha(data)
        assert alpha == 1.0

    def test_cronbach_alpha_random(self):
        """Test Cronbach's alpha on random data (should be low)."""
        n = 1000
        data = pd.DataFrame(np.random.randn(n, 10), columns=[f'q{i}' for i in range(1, 11)])
        alpha = _calculate_cronbach_alpha(data)
        # Random data should have low alpha, but not necessarily negative
        assert alpha < 0.5

class TestPsychometricValidation:
    def test_validate_rses_psychometrics_pass(self):
        """Test validation passes for valid synthetic data."""
        df = generate_synthetic_data(n_samples=200, seed=42)
        # This should not raise
        result = validate_rses_psychometrics(df, min_alpha=0.7)
        assert result is True

    def test_validate_rses_psychometrics_fail(self):
        """Test validation fails for data with low alpha."""
        # Create data with very low internal consistency
        n = 200
        data = pd.DataFrame(np.random.randn(n, 10), columns=[f'q{i}' for i in range(1, 11)])
        
        with pytest.raises(InsufficientSampleError):
            validate_rses_psychometrics(data, min_alpha=0.7)

    def test_validate_rses_missing_items(self):
        """Test validation raises error if RSES items are missing."""
        df = pd.DataFrame({'age': [15, 16]})
        
        with pytest.raises(InsufficientSampleError):
            validate_rses_psychometrics(df)

class TestSyntheticDataGeneration:
    def test_generate_synthetic_data_structure(self):
        """Test that generated data has all required columns."""
        df = generate_synthetic_data(n_samples=100, seed=42)
        
        required_cols = [
            'age', 'gender', 'engagement_count', 'comment_sentiment', 
            'rse_score', 'perceived_social_validation',
            'engagement_timestamp', 'self_report_timestamp'
        ] + [f'q{i}' for i in range(1, 11)]
        
        for col in required_cols:
            assert col in df.columns

    def test_generate_synthetic_data_longitudinal_order(self):
        """Test that engagement_timestamp < self_report_timestamp."""
        df = generate_synthetic_data(n_samples=100, seed=42)
        
        # Convert to comparable format if needed (they are already timestamps)
        # Check a few rows
        for idx in range(min(10, len(df))):
            assert df.loc[idx, 'engagement_timestamp'] < df.loc[idx, 'self_report_timestamp']

    def test_generate_synthetic_data_psychometric_validity(self):
        """Test that generated data passes psychometric validation by default."""
        df = generate_synthetic_data(n_samples=500, seed=42)
        # The function itself validates, so if it returns, it passed.
        # Double check alpha
        rses_items = df[[f'q{i}' for i in range(1, 11)]]
        from data.generator import _calculate_cronbach_alpha
        alpha = _calculate_cronbach_alpha(rses_items)
        assert alpha > 0.7

class TestAssociationRecovery:
    def test_verify_association_recovery(self):
        """Test that association recovery verification runs without error."""
        df = generate_synthetic_data(n_samples=200, seed=42)
        result = verify_association_recovery(df)
        
        assert 'converged' in result
        assert 'status' in result
        # For synthetic data with correct structure, it should converge
        assert result['status'] == 'PASS' or result['converged'] is True