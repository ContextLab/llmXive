import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from generate_aligned_dataset import validate_final_schema

class TestSchemaValidation:
    def test_valid_schema(self):
        """Test that a DataFrame with correct columns passes validation."""
        df = pd.DataFrame({
            'composition': ['A', 'B'],
            'surface_facet': ['111', '100'],
            'energy_change': [0.5, 1.2],
            'd_band_center': [-2.1, -1.5],
            'adsorption_energy': [-3.0, -4.2],
            'extra_descriptor': [1.0, 2.0]
        })
        
        is_valid, errors = validate_final_schema(df)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_target_column(self):
        """Test that missing 'energy_change' fails validation."""
        df = pd.DataFrame({
            'composition': ['A'],
            'surface_facet': ['111'],
            'd_band_center': [-2.1],
            'adsorption_energy': [-3.0]
        })
        
        is_valid, errors = validate_final_schema(df)
        assert is_valid is False
        assert any("Missing required columns" in e and "energy_change" in e for e in errors)

    def test_nan_in_target(self):
        """Test that NaN in 'energy_change' fails validation."""
        df = pd.DataFrame({
            'composition': ['A'],
            'surface_facet': ['111'],
            'energy_change': [np.nan],
            'd_band_center': [-2.1],
            'adsorption_energy': [-3.0]
        })
        
        is_valid, errors = validate_final_schema(df)
        assert is_valid is False
        assert any("NaN" in e for e in errors)

    def test_wrong_type_in_target(self):
        """Test that non-numeric target fails validation."""
        df = pd.DataFrame({
            'composition': ['A'],
            'surface_facet': ['111'],
            'energy_change': ['not_a_number'],
            'd_band_center': [-2.1],
            'adsorption_energy': [-3.0]
        })
        
        is_valid, errors = validate_final_schema(df)
        assert is_valid is False
        assert any("not numeric" in e for e in errors)
