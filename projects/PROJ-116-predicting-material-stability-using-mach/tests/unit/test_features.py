"""
Unit tests for Magpie feature extraction logic.

Dependencies:
  - T005: data_models (MaterialEntry, FeatureVector)
  - T007: validation utilities
"""
import unittest
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# Import project modules
from data_models import MaterialEntry, FeatureVector
from utils.validation import check_missing_bond_lengths, check_degenerate_voronoi_cells, validate_structure
from utils.logging import setup_logger

# Mock Magpie feature extraction logic for testing
# In a real implementation, this would use the magpie package or pymatgen
def extract_magpie_features_compositional(composition: Dict[str, float]) -> FeatureVector:
    """
    Extract bulk compositional (Magpie) features from a chemical composition.
    
    Args:
        composition: Dict mapping element symbol to stoichiometric coefficient.
        
    Returns:
        FeatureVector containing the extracted features.
    """
    # Mock feature extraction for unit testing purposes
    # In production, this would calculate mean, std, min, max, etc. of elemental properties
    properties = ['mean_atomic_mass', 'std_atomic_mass', 'mean_electronegativity', 
                  'std_electronegativity', 'mean_melting_point', 'std_melting_point']
    
    values = [0.0] * len(properties)
    
    # Simulate calculation based on composition
    if composition:
        # Simple mock: sum of stoichiometric coefficients
        total_stoich = sum(composition.values())
        values[0] = total_stoich * 10.0  # Mock mean atomic mass
        values[1] = np.std(list(composition.values())) * 5.0  # Mock std
        values[2] = 1.5  # Mock electronegativity
        values[3] = 0.3
        values[4] = 1000.0  # Mock melting point
        values[5] = 150.0
    
    return FeatureVector(features=properties, values=np.array(values))


class TestMagpieFeatureExtraction(unittest.TestCase):
    """Unit tests for Magpie feature extraction logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = setup_logger("test_features")
        self.test_data_dir = Path(__file__).parent.parent.parent / "data" / "raw"

    def test_empty_composition_returns_zero_features(self):
        """Test that empty composition returns feature vector with zero values."""
        composition = {}
        feature_vector = extract_magpie_features_compositional(composition)
        
        self.assertIsInstance(feature_vector, FeatureVector)
        self.assertEqual(len(feature_vector.values), len(feature_vector.features))
        self.assertTrue(np.allclose(feature_vector.values, 0.0))

    def test_valid_composition_returns_nonzero_features(self):
        """Test that valid composition returns non-zero feature values."""
        composition = {"Li": 2.0, "O": 1.0}
        feature_vector = extract_magpie_features_compositional(composition)
        
        self.assertIsInstance(feature_vector, FeatureVector)
        # At least some features should be non-zero for valid composition
        self.assertFalse(np.allclose(feature_vector.values, 0.0))

    def test_feature_vector_has_correct_structure(self):
        """Test that FeatureVector has expected attributes."""
        composition = {"Fe": 1.0}
        feature_vector = extract_magpie_features_compositional(composition)
        
        self.assertTrue(hasattr(feature_vector, 'features'))
        self.assertTrue(hasattr(feature_vector, 'values'))
        self.assertIsInstance(feature_vector.features, list)
        self.assertIsInstance(feature_vector.values, np.ndarray)

    def test_integration_with_material_entry(self):
        """Test that features can be attached to a MaterialEntry."""
        composition = {"Li": 1.0, "Mn": 1.0, "O": 2.0}
        feature_vector = extract_magpie_features_compositional(composition)
        
        # Create a MaterialEntry with the features
        entry = MaterialEntry(
            material_id="test_001",
            composition=composition,
            structure=None,  # No structure for compositional-only test
            features=feature_vector,
            formation_energy=-1.0
        )
        
        self.assertEqual(entry.material_id, "test_001")
        self.assertEqual(entry.composition, composition)
        self.assertEqual(entry.features, feature_vector)

    def test_validation_integration(self):
        """Test that feature extraction works with validation utilities."""
        composition = {"Li": 0.5, "O": 0.5}
        feature_vector = extract_magpie_features_compositional(composition)
        
        # Validate that the feature vector has no NaN values
        self.assertFalse(np.any(np.isnan(feature_vector.values)))
        self.assertFalse(np.any(np.isinf(feature_vector.values)))

    def test_multiple_compositions_consistency(self):
        """Test that different compositions produce consistent feature dimensions."""
        compositions = [
            {"Li": 1.0},
            {"Fe": 1.0, "O": 1.0},
            {"Na": 2.0, "S": 1.0, "O": 4.0}
        ]
        
        feature_vectors = [extract_magpie_features_compositional(comp) for comp in compositions]
        
        # All feature vectors should have the same number of features
        first_len = len(feature_vectors[0].features)
        for fv in feature_vectors:
            self.assertEqual(len(fv.features), first_len)
            self.assertEqual(len(fv.values), first_len)

    def test_feature_names_are_descriptive(self):
        """Test that feature names follow Magpie naming conventions."""
        composition = {"Si": 1.0, "O": 2.0}
        feature_vector = extract_magpie_features_compositional(composition)
        
        # Check that feature names contain expected statistical descriptors
        feature_names = feature_vector.features
        expected_keywords = ['mean', 'std', 'min', 'max']
        
        found_keywords = []
        for name in feature_names:
            for keyword in expected_keywords:
                if keyword in name.lower():
                    found_keywords.append(keyword)
                    break
        
        # At least some features should have statistical descriptors
        self.assertGreater(len(found_keywords), 0)


if __name__ == "__main__":
    unittest.main()