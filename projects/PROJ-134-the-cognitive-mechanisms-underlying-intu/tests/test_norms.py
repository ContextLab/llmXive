"""
Tests for the norms module.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.norms import (
    load_norms_data,
    save_norms_data,
    get_means,
    get_std_devs,
    get_correlation_matrix,
    get_covariance_matrix,
    generate_synthetic_mfq_from_norms,
    validate_against_norms,
    load_gervais_norms
)

class TestNormsLoading:
    """Test norms loading functionality."""
    
    def test_load_norms_data_returns_dict(self):
        """Test that load_norms_data returns a dictionary."""
        norms = load_norms_data()
        assert isinstance(norms, dict)
        assert 'means' in norms or len(norms) > 0
    
    def test_load_gervais_norms_alias(self):
        """Test that load_gervais_norms works as an alias."""
        norms = load_gervais_norms()
        assert isinstance(norms, dict)
    
    def test_get_means_returns_correct_keys(self):
        """Test that get_means returns all foundation keys."""
        means = get_means()
        expected_keys = [
            'care_harm', 'fairness_cheating', 'loyalty_betrayal',
            'authority_subversion', 'sanction_pollution', 'liberty_oppression'
        ]
        for key in expected_keys:
            assert key in means
    
    def test_get_std_devs_returns_correct_keys(self):
        """Test that get_std_devs returns all foundation keys."""
        stds = get_std_devs()
        expected_keys = [
            'care_harm', 'fairness_cheating', 'loyalty_betrayal',
            'authority_subversion', 'sanction_pollution', 'liberty_oppression'
        ]
        for key in expected_keys:
            assert key in stds
    
    def test_get_correlation_matrix_shape(self):
        """Test that correlation matrix has correct shape."""
        corr_matrix = get_correlation_matrix()
        assert corr_matrix.shape == (6, 6)
    
    def test_get_covariance_matrix_shape(self):
        """Test that covariance matrix has correct shape."""
        cov_matrix = get_covariance_matrix()
        assert cov_matrix.shape == (6, 6)
    
    def test_covariance_matrix_is_positive_semidefinite(self):
        """Test that covariance matrix is positive semidefinite."""
        cov_matrix = get_covariance_matrix()
        eigenvalues = np.linalg.eigvalsh(cov_matrix)
        assert all(eigenvalues >= -1e-10)  # Allow small numerical errors

class TestSyntheticDataGeneration:
    """Test synthetic data generation."""
    
    def test_generate_synthetic_mfq_returns_dataframe(self):
        """Test that generate_synthetic_mfq_from_norms returns a DataFrame."""
        df = generate_synthetic_mfq_from_norms(n_samples=50, seed=42)
        assert isinstance(df, pd.DataFrame)
    
    def test_generate_synthetic_mfq_correct_shape(self):
        """Test that generated data has correct shape."""
        df = generate_synthetic_mfq_from_norms(n_samples=100, seed=42)
        assert df.shape[0] == 100
        assert df.shape[1] >= 6  # At least 6 foundations + participant_id + timestamp
    
    def test_generate_synthetic_mfq_values_in_range(self):
        """Test that generated values are in valid range [1, 7]."""
        df = generate_synthetic_mfq_from_norms(n_samples=100, seed=42)
        foundations = ['care_harm', 'fairness_cheating', 'loyalty_betrayal',
                     'authority_subversion', 'sanction_pollution', 'liberty_oppression']
        for foundation in foundations:
            assert df[foundation].min() >= 1
            assert df[foundation].max() <= 7
    
    def test_generate_synthetic_mfq_reproducibility(self):
        """Test that same seed produces same results."""
        df1 = generate_synthetic_mfq_from_norms(n_samples=50, seed=123)
        df2 = generate_synthetic_mfq_from_norms(n_samples=50, seed=123)
        assert df1.equals(df2)

class TestValidation:
    """Test validation against norms."""
    
    def test_validate_against_norms_returns_dict(self):
        """Test that validate_against_norms returns a dictionary."""
        df = generate_synthetic_mfq_from_norms(n_samples=100, seed=42)
        results = validate_against_norms(df)
        assert isinstance(results, dict)
        assert 'passed' in results
        assert 'metrics' in results
    
    def test_validate_synthetic_data_passes(self):
        """Test that synthetic data generated from norms passes validation."""
        df = generate_synthetic_mfq_from_norms(n_samples=1000, seed=42)
        results = validate_against_norms(df, tolerance_sd=2.0)
        # With large sample and high tolerance, should pass
        assert results['passed'] or len(results.get('failures', [])) == 0
    
    def test_validate_with_wrong_data_fails(self):
        """Test that data far from norms fails validation."""
        # Create data with means far from expected
        df = pd.DataFrame({
            'care_harm': [7.0] * 100,
            'fairness_cheating': [7.0] * 100,
            'loyalty_betrayal': [7.0] * 100,
            'authority_subversion': [7.0] * 100,
            'sanction_pollution': [7.0] * 100,
            'liberty_oppression': [7.0] * 100,
            'participant_id': range(1, 101)
        })
        results = validate_against_norms(df, tolerance_sd=0.5)
        # Should fail because means are far from expected
        assert not results['passed'] or len(results.get('failures', [])) > 0

class TestIntegration:
    """Integration tests for norms module."""
    
    def test_full_pipeline(self):
        """Test full pipeline: load, generate, validate."""
        # Load norms
        norms = load_norms_data()
        assert norms is not None
        
        # Generate data
        df = generate_synthetic_mfq_from_norms(n_samples=200, seed=42)
        assert df is not None
        assert len(df) == 200
        
        # Validate
        results = validate_against_norms(df)
        assert 'passed' in results
        assert 'metrics' in results
    
    def test_save_and_load_norms(self):
        """Test saving and reloading norms."""
        from code.config import get_path
        import tempfile
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            norms = load_norms_data()
            save_norms_data(norms, temp_path)
            
            # Reload
            reloaded = load_norms_data(temp_path)
            
            # Check means match
            for key in norms.get('means', {}):
                if key in norms.get('means', {}) and key in reloaded.get('means', {}):
                    assert norms['means'][key] == reloaded['means'][key]
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)