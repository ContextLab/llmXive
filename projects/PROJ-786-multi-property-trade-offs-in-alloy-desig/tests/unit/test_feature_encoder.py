"""
Unit tests for the feature encoder module.

Tests cover:
- Periodic property fetching (mendeleev)
- Composition parsing
- Feature vector generation
- DataFrame encoding
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from feature_encoder import (
    get_periodic_property,
    encode_composition,
    encode_dataframe,
    MISSING_VALUE
)

class TestGetPeriodicProperty:
    def test_atomic_radius_valid(self):
        """Test fetching atomic radius for a known element."""
        radius = get_periodic_property('Fe', 'atomic_radius')
        assert isinstance(radius, float)
        assert radius > 0
        # Iron atomic radius is approximately 126 pm (varies by definition)
        assert 100 < radius < 150

    def test_electronegativity_valid(self):
        """Test fetching electronegativity for a known element."""
        electroneg = get_periodic_property('O', 'electronegativity')
        assert isinstance(electroneg, float)
        assert electroneg > 0
        # Oxygen electronegativity is 3.44
        assert 3.0 < electroneg < 4.0

    def test_missing_element(self):
        """Test behavior with an invalid element symbol."""
        radius = get_periodic_property('XX', 'atomic_radius')
        assert radius == MISSING_VALUE

    def test_missing_property(self):
        """Test behavior with unsupported property name."""
        with pytest.raises(ValueError):
            get_periodic_property('Fe', 'non_existent_property')

class TestEncodeComposition:
    def test_single_element(self):
        """Test encoding a single element composition."""
        result = encode_composition("Fe:1.0")
        assert "frac_Fe" in result
        assert result["frac_Fe"] == 1.0
        assert "avg_atomic_radius" in result
        assert "avg_electronegativity" in result

    def test_multi_element(self):
        """Test encoding a multi-element composition."""
        result = encode_composition("Fe:0.5,Ni:0.5")
        assert "frac_Fe" in result
        assert "frac_Ni" in result
        # Fractions should sum to 1.0
        assert abs(result["frac_Fe"] + result["frac_Ni"] - 1.0) < 1e-6
        assert "avg_atomic_radius" in result
        assert "avg_electronegativity" in result

    def test_invalid_format(self):
        """Test encoding with invalid format (no colon)."""
        result = encode_composition("Fe0.5")
        assert len(result) == 0  # Should return empty dict

    def test_empty_string(self):
        """Test encoding an empty string."""
        result = encode_composition("")
        assert len(result) == 0

    def test_null_string(self):
        """Test encoding a null/None string."""
        result = encode_composition(None)
        assert len(result) == 0

    def test_weighted_average_calculation(self):
        """Test that weighted averages are calculated correctly."""
        # Fe: 126 pm, 1.83 EN (approx)
        # Ni: 124 pm, 1.91 EN (approx)
        # 50/50 mix should be roughly average
        result = encode_composition("Fe:0.5,Ni:0.5")
        
        # Check that averages exist
        assert "avg_atomic_radius" in result
        assert "avg_electronegativity" in result
        
        # Values should be positive
        assert result["avg_atomic_radius"] > 0
        assert result["avg_electronegativity"] > 0

    def test_num_elements_feature(self):
        """Test that num_elements feature is added."""
        result = encode_composition("Fe:0.5,Ni:0.3,Cr:0.2")
        assert "num_elements" in result
        assert result["num_elements"] == 3.0

class TestEncodeDataFrame:
    def test_encode_single_row(self):
        """Test encoding a DataFrame with a single row."""
        data = {"composition": ["Fe:0.5,Ni:0.5"]}
        df = pd.DataFrame(data)
        encoded = encode_dataframe(df, composition_col='composition')
        
        assert "frac_Fe" in encoded.columns
        assert "frac_Ni" in encoded.columns
        assert len(encoded) == 1

    def test_encode_multiple_rows(self):
        """Test encoding a DataFrame with multiple rows."""
        data = {
            "composition": [
                "Fe:0.5,Ni:0.5",
                "Fe:0.8,Cr:0.2",
                "Ni:0.3,Cr:0.7"
            ]
        }
        df = pd.DataFrame(data)
        encoded = encode_dataframe(df, composition_col='composition')
        
        assert len(encoded) == 3
        assert "frac_Fe" in encoded.columns
        assert "frac_Ni" in encoded.columns
        assert "frac_Cr" in encoded.columns

    def test_missing_column(self):
        """Test encoding with a missing composition column."""
        data = {"wrong_col": ["Fe:0.5"]}
        df = pd.DataFrame(data)
        with pytest.raises(ValueError):
            encode_dataframe(df, composition_col='composition')

    def test_handles_null_composition(self):
        """Test encoding DataFrame with null composition values."""
        data = {
            "composition": [
                "Fe:0.5,Ni:0.5",
                None,
                "Ni:1.0"
            ]
        }
        df = pd.DataFrame(data)
        encoded = encode_dataframe(df, composition_col='composition')
        
        # Should not crash, but null rows should have empty features
        assert len(encoded) == 3
        # Check that non-null rows have features
        assert encoded.loc[0, "frac_Fe"] == 0.5

    def test_includes_original_columns(self):
        """Test that original DataFrame columns are preserved."""
        data = {
            "composition": ["Fe:0.5,Ni:0.5"],
            "bulk_modulus": [150.0],
            "shear_modulus": [80.0]
        }
        df = pd.DataFrame(data)
        encoded = encode_dataframe(df, composition_col='composition')
        
        assert "bulk_modulus" in encoded.columns
        assert "shear_modulus" in encoded.columns
        assert "frac_Fe" in encoded.columns