"""
Tests for the descriptor engine.
"""
import pytest
import pandas as pd
import numpy as np
from features.descriptor_engine import DescriptorEngine


class TestDescriptorEngine:
    """Test cases for DescriptorEngine class."""
    
    @pytest.fixture
    def sample_compositions(self):
        """Create sample composition DataFrame."""
        return pd.DataFrame({
            'Sn': [0.95, 0.60, 0.50],
            'Ag': [0.03, 0.05, 0.20],
            'Cu': [0.02, 0.35, 0.30],
            'alloy_id': [1, 2, 3]
        })
    
    def test_weighted_mean_atomic_mass(self, sample_compositions):
        """Test weighted mean atomic mass calculation."""
        engine = DescriptorEngine()
        descriptors = engine.compute_all_descriptors(sample_compositions)
        
        assert 'weighted_mean_atomic_mass' in descriptors.columns
        # Sn (118.71) dominates in first row, so value should be close to Sn's mass
        assert descriptors.loc[0, 'weighted_mean_atomic_mass'] > 100
    
    def test_valence_electron_concentration(self, sample_compositions):
        """Test VEC calculation."""
        engine = DescriptorEngine()
        descriptors = engine.compute_all_descriptors(sample_compositions)
        
        assert 'valence_electron_concentration' in descriptors.columns
        # Sn has 4 valence electrons, so pure Sn should be close to 4
        assert descriptors.loc[0, 'valence_electron_concentration'] > 3.5
    
    def test_variance_descriptors(self, sample_compositions):
        """Test variance descriptors are computed."""
        engine = DescriptorEngine()
        descriptors = engine.compute_all_descriptors(sample_compositions)
        
        assert 'electronegativity_variance' in descriptors.columns
        assert 'atomic_radius_variance' in descriptors.columns
        
        # Variance should be non-negative
        assert all(descriptors['electronegativity_variance'] >= 0)
        assert all(descriptors['atomic_radius_variance'] >= 0)
    
    def test_descriptor_names(self):
        """Test that descriptor names are returned correctly."""
        engine = DescriptorEngine()
        names = engine.get_descriptor_names()
        
        expected = [
            'weighted_mean_atomic_mass',
            'electronegativity_variance',
            'atomic_radius_variance',
            'weighted_mean_melting_point',
            'valence_electron_concentration'
        ]
        
        assert names == expected
    
    def test_zero_sum_handling(self):
        """Test handling of zero-sum compositions."""
        engine = DescriptorEngine()
        df = pd.DataFrame({
            'Sn': [0.0, 0.5],
            'Ag': [0.0, 0.5]
        })
        
        # Should not crash, but may produce NaN or warnings
        descriptors = engine.compute_all_descriptors(df)
        
        # At least some values should be computed
        assert descriptors.shape[0] == 2
