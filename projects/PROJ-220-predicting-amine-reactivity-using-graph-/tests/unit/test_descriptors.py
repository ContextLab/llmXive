"""
Unit tests for molecular descriptor calculations.

Tests verify:
- Individual descriptor functions return expected types and ranges
- aggregate_independent_vector returns a valid 10-element vector
- No NaN values in the output vector for valid molecules
- Batch processing works correctly
"""

import numpy as np
import pytest
from rdkit import Chem
from src.data.descriptors import (
    compute_hammett,
    compute_taft_charton,
    compute_verloop,
    compute_mr,
    aggregate_independent_vector,
    aggregate_independent_vector_batch,
    get_descriptor_names,
    get_descriptor_count
)

# Test molecules
VALID_SMILES = [
    "CCN",  # Ethylamine
    "CN",   # Methylamine
    "CC(C)N",  # Isopropylamine
    "c1ccccc1N",  # Aniline
    "CC(=O)N",  # Acetamide
]

INVALID_SMILES = [
    "invalid_smiles",
    "",
    "C1CC1",  # Invalid ring closure
]

class TestHammett:
    def test_returns_dict(self):
        """Test that compute_hammett returns a dictionary."""
        result = compute_hammett("CCN")
        assert isinstance(result, dict)
    
    def test_has_required_keys(self):
        """Test that all required keys are present."""
        result = compute_hammett("CCN")
        required_keys = ['sigma_p', 'sigma_m', 'sigma_plus', 'sigma_minus']
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
    
    def test_values_are_floats(self):
        """Test that all values are floats."""
        result = compute_hammett("CCN")
        for value in result.values():
            assert isinstance(value, (int, float))
    
    def test_returns_zero_for_non_aromatic(self):
        """Test that non-aromatic molecules return zeros."""
        result = compute_hammett("CCN")
        assert result['sigma_p'] == 0.0
        assert result['sigma_m'] == 0.0

class TestTaftCharton:
    def test_returns_dict(self):
        """Test that compute_taft_charton returns a dictionary."""
        result = compute_taft_charton("CCN")
        assert isinstance(result, dict)
    
    def test_has_required_keys(self):
        """Test that all required keys are present."""
        result = compute_taft_charton("CCN")
        required_keys = ['Es', 'Es_s', 'nu']
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
    
    def test_values_are_floats(self):
        """Test that all values are floats."""
        result = compute_taft_charton("CCN")
        for value in result.values():
            assert isinstance(value, (int, float))

class TestVerloop:
    def test_returns_dict(self):
        """Test that compute_verloop returns a dictionary."""
        result = compute_verloop("CCN")
        assert isinstance(result, dict)
    
    def test_has_required_keys(self):
        """Test that all required keys are present."""
        result = compute_verloop("CCN")
        required_keys = ['B1', 'B5']
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
    
    def test_values_are_floats(self):
        """Test that all values are floats."""
        result = compute_verloop("CCN")
        for value in result.values():
            assert isinstance(value, (int, float))

class TestMR:
    def test_returns_float(self):
        """Test that compute_mr returns a float."""
        result = compute_mr("CCN")
        assert isinstance(result, (int, float))
    
    def test_non_negative(self):
        """Test that MR is non-negative."""
        result = compute_mr("CCN")
        assert result >= 0.0

class TestAggregateIndependentVector:
    def test_returns_numpy_array(self):
        """Test that aggregate_independent_vector returns a numpy array."""
        result = aggregate_independent_vector("CCN")
        assert isinstance(result, np.ndarray)
    
    def test_vector_length_is_10(self):
        """Test that the vector has exactly 10 elements."""
        result = aggregate_independent_vector("CCN")
        assert len(result) == 10, f"Expected 10 elements, got {len(result)}"
    
    def test_no_nan_values(self):
        """Test that the vector contains no NaN values."""
        result = aggregate_independent_vector("CCN")
        assert not np.any(np.isnan(result)), "Vector contains NaN values"
    
    def test_all_descriptors_present_for_test_molecule(self):
        """
        Verification test: Vector contains non-NaN values for all 10 descriptors
        for a test molecule (as required by task specification).
        """
        # Use a simple amine molecule
        test_smiles = "CCN"  # Ethylamine
        vector = aggregate_independent_vector(test_smiles)
        
        # Check length
        assert len(vector) == 10, f"Vector length should be 10, got {len(vector)}"
        
        # Check no NaN values
        nan_mask = np.isnan(vector)
        assert not np.any(nan_mask), f"Vector contains NaN at indices: {np.where(nan_mask)[0]}"
        
        # Check all values are finite (not inf)
        assert np.all(np.isfinite(vector)), "Vector contains infinite values"
        
        # Check that values are not all zeros (at least some descriptors should have non-zero values)
        # Note: This is a soft check as some descriptors might legitimately be zero
        non_zero_count = np.sum(np.abs(vector) > 1e-10)
        assert non_zero_count > 0, "All descriptor values are zero (unexpected)"
    
    def test_raises_on_invalid_smiles(self):
        """Test that invalid SMILES raises ValueError."""
        with pytest.raises(ValueError):
            aggregate_independent_vector("invalid_smiles")
    
    def test_consistent_order(self):
        """Test that the vector order is consistent."""
        names = get_descriptor_names()
        assert len(names) == 10, f"Expected 10 descriptor names, got {len(names)}"
        
        expected_names = [
            'sigma_p', 'sigma_m', 'sigma_plus', 'sigma_minus',
            'Es', 'Es_s', 'nu',
            'B1', 'B5',
            'MR'
        ]
        assert names == expected_names, f"Descriptor names mismatch: {names} vs {expected_names}"

class TestBatchProcessing:
    def test_returns_2d_array(self):
        """Test that batch processing returns a 2D array."""
        result = aggregate_independent_vector_batch(["CCN", "CN"])
        assert result.ndim == 2, f"Expected 2D array, got {result.ndim}D"
    
    def test_correct_shape(self):
        """Test that batch processing returns correct shape."""
        result = aggregate_independent_vector_batch(["CCN", "CN", "CC(C)N"])
        assert result.shape == (3, 10), f"Expected shape (3, 10), got {result.shape}"
    
    def test_no_nan_in_batch(self):
        """Test that batch processing produces no NaN values."""
        result = aggregate_independent_vector_batch(VALID_SMILES)
        assert not np.any(np.isnan(result)), "Batch result contains NaN values"
    
    def test_handles_invalid_smiles_in_batch(self):
        """Test that invalid SMILES in batch are handled gracefully."""
        mixed_smiles = ["CCN", "invalid", "CN"]
        result = aggregate_independent_vector_batch(mixed_smiles)
        
        # Should have 3 rows
        assert result.shape[0] == 3, f"Expected 3 rows, got {result.shape[0]}"
        
        # First and third should be non-zero (valid molecules)
        assert np.any(result[0] != 0), "First molecule should have non-zero descriptors"
        assert np.any(result[2] != 0), "Third molecule should have non-zero descriptors"
        
        # Second should be all zeros (invalid molecule)
        assert np.all(result[1] == 0), "Invalid molecule should have zero descriptors"

class TestDescriptorNames:
    def test_returns_list(self):
        """Test that get_descriptor_names returns a list."""
        result = get_descriptor_names()
        assert isinstance(result, list)
    
    def test_correct_count(self):
        """Test that the correct number of descriptor names is returned."""
        result = get_descriptor_names()
        assert len(result) == 10, f"Expected 10 names, got {len(result)}"
    
    def test_descriptor_count_function(self):
        """Test that get_descriptor_count returns 10."""
        count = get_descriptor_count()
        assert count == 10, f"Expected 10, got {count}"

class TestIntegration:
    def test_full_workflow(self):
        """Test the full workflow from SMILES to aggregated vector."""
        for smiles in VALID_SMILES:
            # Test individual functions
            hammett = compute_hammett(smiles)
            taft = compute_taft_charton(smiles)
            verloop = compute_verloop(smiles)
            mr = compute_mr(smiles)
            
            # Verify types
            assert isinstance(hammett, dict)
            assert isinstance(taft, dict)
            assert isinstance(verloop, dict)
            assert isinstance(mr, (int, float))
            
            # Test aggregation
            vector = aggregate_independent_vector(smiles)
            assert isinstance(vector, np.ndarray)
            assert len(vector) == 10
            assert not np.any(np.isnan(vector))
    
    def test_vector_values_reasonable(self):
        """Test that vector values are within reasonable ranges."""
        vector = aggregate_independent_vector("CCN")
        
        # Check ranges for different descriptor types
        # Hammett sigma: typically -1.5 to 2.0
        assert np.all(np.abs(vector[0:4]) < 3.0), "Hammett values out of range"
        
        # Taft Es: typically -0.5 to 0.5
        assert np.all(np.abs(vector[4:7]) < 1.0), "Taft values out of range"
        
        # Verloop B1, B5: typically 1.0 to 3.0
        assert np.all((vector[7:9] >= 0.5) & (vector[7:9] <= 5.0)), "Verloop values out of range"
        
        # MR: typically 0 to 100
        assert 0 <= vector[9] <= 200, "MR value out of range"