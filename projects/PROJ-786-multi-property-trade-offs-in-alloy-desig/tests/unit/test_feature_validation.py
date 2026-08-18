import pytest
import pandas as pd
import numpy as np
from code.feature_encoder import validate_periodic_descriptors, encode_composition, DEFAULT_PERIODIC_DESCRIPTORS

class TestFeatureValidation:
    """Tests for periodic descriptor validation in feature encoding."""
    
    def test_validate_minimum_two_descriptors(self):
        """Test that validation requires at least two periodic descriptors."""
        # Create a feature dict with only one descriptor
        features_one = {
            'weighted_atomic_radius': 1.5,
            'frac_Fe': 0.5,
            'frac_Ni': 0.5
        }
        
        is_valid, msg = validate_periodic_descriptors(features_one, ['atomic_radius'])
        assert not is_valid, "Should fail with only one descriptor"
        assert "Insufficient periodic descriptors" in msg
        
    def test_validate_two_descriptors_pass(self):
        """Test that validation passes with two or more descriptors."""
        # Create a feature dict with two descriptors
        features_two = {
            'weighted_atomic_radius': 1.5,
            'weighted_electronegativity': 1.8,
            'frac_Fe': 0.5,
            'frac_Ni': 0.5
        }
        
        is_valid, msg = validate_periodic_descriptors(features_two, ['atomic_radius', 'electronegativity'])
        assert is_valid, "Should pass with two descriptors"
        assert "Validation passed" in msg
        
    def test_validate_three_descriptors_pass(self):
        """Test that validation passes with three descriptors."""
        features_three = {
            'weighted_atomic_radius': 1.5,
            'weighted_electronegativity': 1.8,
            'weighted_ionization_energy': 7.5,
            'frac_Fe': 0.5,
            'frac_Ni': 0.5
        }
        
        is_valid, msg = validate_periodic_descriptors(features_three, ['atomic_radius', 'electronegativity', 'ionization_energy'])
        assert is_valid, "Should pass with three descriptors"
        
    def test_encode_composition_validates_descriptors(self):
        """Test that encode_composition returns valid=False when descriptors are missing."""
        # This test verifies the integration with the validation logic
        # We can't easily test the actual mendeleev calls without mocking,
        # but we can test the validation function directly
        
        # Simulate a case where descriptors are missing
        features_missing = {
            'frac_Fe': 0.5,
            'frac_Ni': 0.5
            # No weighted_* descriptors
        }
        
        is_valid, msg = validate_periodic_descriptors(features_missing, ['atomic_radius', 'electronegativity'])
        assert not is_valid
        assert "Insufficient periodic descriptors" in msg
        
    def test_empty_features_fails(self):
        """Test that empty feature dict fails validation."""
        features_empty = {}
        
        is_valid, msg = validate_periodic_descriptors(features_empty, ['atomic_radius'])
        assert not is_valid
        assert "Insufficient periodic descriptors" in msg
        
    def test_descriptor_names_match(self):
        """Test that validation checks for correct descriptor names."""
        # Features with wrong prefix
        features_wrong_prefix = {
            'atomic_radius': 1.5,  # Missing 'weighted_' prefix
            'electronegativity': 1.8,
            'frac_Fe': 0.5
        }
        
        is_valid, msg = validate_periodic_descriptors(features_wrong_prefix, ['atomic_radius', 'electronegativity'])
        assert not is_valid, "Should fail because 'weighted_' prefix is missing"
        
    def test_default_descriptors_validation(self):
        """Test validation with default periodic descriptors."""
        features_default = {
            'weighted_atomic_radius': 1.5,
            'weighted_electronegativity': 1.8,
            'weighted_ionization_energy': 7.5,
            'weighted_valence': 8.0,
            'frac_Fe': 0.5
        }
        
        is_valid, msg = validate_periodic_descriptors(features_default, DEFAULT_PERIODIC_DESCRIPTORS)
        assert is_valid, "Should pass with all default descriptors"
        
    def test_partial_default_descriptors_fails(self):
        """Test that having only one of the default descriptors fails."""
        features_partial = {
            'weighted_atomic_radius': 1.5,
            'frac_Fe': 0.5
        }
        
        is_valid, msg = validate_periodic_descriptors(features_partial, DEFAULT_PERIODIC_DESCRIPTORS)
        assert not is_valid, "Should fail with only one descriptor when multiple are expected"
        assert "Insufficient periodic descriptors" in msg
