"""
Unit tests for normalization logic in the HEA data pipeline.

Tests verify that composition normalization correctly enforces sum=1.0
and handles edge cases as specified in the project requirements.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.validators import normalize_compositions, ValidationError
from utils.seeds import set_seed


class TestNormalizeCompositions:
    """Test suite for the normalize_compositions function."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        set_seed(42)
        
    def test_normalize_simple_composition(self):
        """Test normalization of a simple, non-normalized composition."""
        # Input: elements sum to 2.0 (should be normalized to 1.0)
        data = {
            'composition': [
                {'Fe': 0.4, 'Ni': 0.4, 'Co': 0.2},  # Sum = 1.0
                {'Cr': 0.3, 'Mn': 0.3, 'Fe': 0.3, 'Ni': 0.1}  # Sum = 1.0
            ]
        }
        df = pd.DataFrame(data)
        
        result = normalize_compositions(df)
        
        # Verify sums are exactly 1.0
        for comp in result['composition']:
            total = sum(comp.values())
            assert abs(total - 1.0) < 1e-9, f"Composition sum {total} is not 1.0"

    def test_normalize_adjusts_sum_to_one(self):
        """Test that compositions summing to != 1.0 are correctly adjusted."""
        data = {
            'composition': [
                {'Fe': 0.5, 'Ni': 0.5, 'Co': 0.5},  # Sum = 1.5
                {'Cr': 0.2, 'Mn': 0.2, 'Fe': 0.2, 'Ni': 0.1}  # Sum = 0.7
            ]
        }
        df = pd.DataFrame(data)
        
        result = normalize_compositions(df)
        
        # Verify sums are exactly 1.0
        for comp in result['composition']:
            total = sum(comp.values())
            assert abs(total - 1.0) < 1e-9, f"Composition sum {total} is not 1.0"
        
        # Verify relative proportions are preserved
        # First row: Fe:Ni:Co should be 1:1:1
        original_ratio = 0.5 / 0.5
        new_ratio = result['composition'][0]['Fe'] / result['composition'][0]['Ni']
        assert abs(original_ratio - new_ratio) < 1e-9

    def test_normalize_handles_empty_composition(self):
        """Test behavior with empty composition dictionary."""
        data = {
            'composition': [
                {},
                {'Fe': 1.0}
            ]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValidationError, match="Empty composition"):
            normalize_compositions(df)

    def test_normalize_handles_zero_values(self):
        """Test normalization with zero values in composition."""
        data = {
            'composition': [
                {'Fe': 0.0, 'Ni': 0.5, 'Co': 0.5},  # Sum = 1.0
                {'Cr': 0.0, 'Mn': 0.0, 'Fe': 1.0}  # Sum = 1.0
            ]
        }
        df = pd.DataFrame(data)
        
        result = normalize_compositions(df)
        
        # Verify sums are exactly 1.0
        for comp in result['composition']:
            total = sum(comp.values())
            assert abs(total - 1.0) < 1e-9, f"Composition sum {total} is not 1.0"
        
        # Verify zero values remain zero
        assert result['composition'][0]['Fe'] == 0.0
        assert result['composition'][1]['Cr'] == 0.0
        assert result['composition'][1]['Mn'] == 0.0

    def test_normalize_preserves_element_names(self):
        """Test that element names are preserved during normalization."""
        data = {
            'composition': [
                {'Fe': 0.4, 'Ni': 0.4, 'Co': 0.2},
                {'Cr': 0.3, 'Mn': 0.3, 'Fe': 0.3, 'Ni': 0.1}
            ]
        }
        df = pd.DataFrame(data)
        
        result = normalize_compositions(df)
        
        # Check element names are preserved
        assert set(result['composition'][0].keys()) == {'Fe', 'Ni', 'Co'}
        assert set(result['composition'][1].keys()) == {'Cr', 'Mn', 'Fe', 'Ni'}

    def test_normalize_with_negative_values(self):
        """Test that negative values raise a validation error."""
        data = {
            'composition': [
                {'Fe': -0.1, 'Ni': 0.6, 'Co': 0.5}  # Sum = 1.0 but has negative
            ]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValidationError, match="Negative composition value"):
            normalize_compositions(df)

    def test_normalize_large_dataset(self):
        """Test normalization performance and correctness on a larger dataset."""
        set_seed(123)
        
        n_samples = 1000
        compositions = []
        
        for _ in range(n_samples):
            # Generate random composition
            n_elements = np.random.randint(3, 8)
            elements = ['Fe', 'Ni', 'Co', 'Cr', 'Mn', 'Al', 'Cu', 'Ti', 'V', 'Nb'][:n_elements]
            values = np.random.rand(n_elements)
            comp = dict(zip(elements, values))
            compositions.append(comp)
        
        data = {'composition': compositions}
        df = pd.DataFrame(data)
        
        result = normalize_compositions(df)
        
        # Verify all compositions sum to 1.0
        for comp in result['composition']:
            total = sum(comp.values())
            assert abs(total - 1.0) < 1e-9, f"Composition sum {total} is not 1.0"

    def test_normalize_with_single_element(self):
        """Test normalization with a single element (should remain 1.0)."""
        data = {
            'composition': [
                {'Fe': 1.0},
                {'Ni': 2.0}  # Should be normalized to 1.0
            ]
        }
        df = pd.DataFrame(data)
        
        result = normalize_compositions(df)
        
        assert result['composition'][0]['Fe'] == 1.0
        assert result['composition'][1]['Ni'] == 1.0

    def test_normalize_with_float_precision(self):
        """Test that normalization handles floating point precision correctly."""
        # Use values that might cause floating point issues
        data = {
            'composition': [
                {'Fe': 0.333333333, 'Ni': 0.333333333, 'Co': 0.333333334}
            ]
        }
        df = pd.DataFrame(data)
        
        result = normalize_compositions(df)
        
        total = sum(result['composition'][0].values())
        # Allow for small floating point errors
        assert abs(total - 1.0) < 1e-6, f"Composition sum {total} exceeds precision tolerance"

    def test_normalize_returns_dataframe(self):
        """Test that the function returns a pandas DataFrame."""
        data = {
            'composition': [
                {'Fe': 0.5, 'Ni': 0.5}
            ]
        }
        df = pd.DataFrame(data)
        
        result = normalize_compositions(df)
        
        assert isinstance(result, pd.DataFrame)
        assert 'composition' in result.columns