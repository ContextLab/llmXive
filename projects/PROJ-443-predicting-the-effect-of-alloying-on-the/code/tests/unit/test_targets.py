"""
Unit tests for target calculation in src/features/targets.py
"""
import pytest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.features.targets import (
    calculate_miedema_bulk_modulus,
    compute_residual_target,
    get_elemental_bulk_modulus,
    OBSERVED_BULK_MODULUS_COL,
    MIEDEMA_BULK_MODULUS_COL,
    RESIDUAL_TARGET_COL,
    DIAGNOSTIC_BULK_MODULUS_COL
)

class TestTargetCalculation:
    """Test suite for target calculation functions."""

    def test_get_elemental_bulk_modulus_known(self):
        """Test getting bulk modulus for known elements."""
        assert get_elemental_bulk_modulus("Fe") > 0
        assert get_elemental_bulk_modulus("Ni") > 0
        assert get_elemental_bulk_modulus("Al") > 0

    def test_get_elemental_bulk_modulus_unknown(self):
        """Test getting bulk modulus for unknown element."""
        assert get_elemental_bulk_modulus("Xx") == 0.0

    def test_calculate_miedema_bulk_modulus_simple(self):
        """Test Miedema calculation with simple composition."""
        # Equal parts Fe and Ni
        composition = {"Fe": 0.5, "Ni": 0.5}
        result = calculate_miedema_bulk_modulus(composition)
        
        # Expected: (170 + 180) / 2 = 175
        expected = (170.0 * 0.5) + (180.0 * 0.5)
        assert np.isclose(result, expected, rtol=1e-5)

    def test_calculate_miedema_bulk_modulus_empty(self):
        """Test Miedema calculation with empty composition."""
        result = calculate_miedema_bulk_modulus({})
        assert result == 0.0

    def test_calculate_miedema_bulk_modulus_single_element(self):
        """Test Miedema calculation with single element."""
        composition = {"Fe": 1.0}
        result = calculate_miedema_bulk_modulus(composition)
        assert np.isclose(result, 170.0, rtol=1e-5)

    def test_compute_residual_target_basic(self):
        """Test basic residual target computation."""
        sample_data = {
            "composition": [{"Fe": 0.5, "Ni": 0.5}],
            "Bulk_Modulus_Observed": [180.0]
        }
        df = pd.DataFrame(sample_data)
        
        result_df = compute_residual_target(df)
        
        # Check columns exist
        assert MIEDEMA_BULK_MODULUS_COL in result_df.columns
        assert RESIDUAL_TARGET_COL in result_df.columns
        assert DIAGNOSTIC_BULK_MODULUS_COL in result_df.columns

    def test_compute_residual_target_values(self):
        """Test that residual values are calculated correctly."""
        # Fe (170) + Ni (180) -> Miedema = 175
        # Observed = 180
        # Residual = 180 - 175 = 5
        sample_data = {
            "composition": [{"Fe": 0.5, "Ni": 0.5}],
            "Bulk_Modulus_Observed": [180.0]
        }
        df = pd.DataFrame(sample_data)
        
        result_df = compute_residual_target(df)
        
        miedema_val = result_df[MIEDEMA_BULK_MODULUS_COL].iloc[0]
        residual_val = result_df[RESIDUAL_TARGET_COL].iloc[0]
        
        assert np.isclose(miedema_val, 175.0, rtol=1e-5)
        assert np.isclose(residual_val, 5.0, rtol=1e-5)

    def test_compute_residual_target_missing_observed(self):
        """Test error when observed column is missing."""
        sample_data = {
            "composition": [{"Fe": 0.5, "Ni": 0.5}]
        }
        df = pd.DataFrame(sample_data)
        
        with pytest.raises(ValueError, match="Required column.*not found"):
            compute_residual_target(df)

    def test_compute_residual_target_missing_composition(self):
        """Test error when composition column is missing."""
        sample_data = {
            "Bulk_Modulus_Observed": [180.0]
        }
        df = pd.DataFrame(sample_data)
        
        with pytest.raises(ValueError, match="Required column.*not found"):
            compute_residual_target(df)

    def test_compute_residual_target_multiple_rows(self):
        """Test residual calculation with multiple rows."""
        sample_data = {
            "composition": [
                {"Fe": 0.5, "Ni": 0.5},
                {"Al": 0.5, "Ti": 0.5},
                {"Nb": 0.5, "Mo": 0.5}
            ],
            "Bulk_Modulus_Observed": [180.0, 150.0, 200.0]
        }
        df = pd.DataFrame(sample_data)
        
        result_df = compute_residual_target(df)
        
        assert len(result_df) == 3
        assert not result_df[RESIDUAL_TARGET_COL].isna().any()

    def test_compute_residual_target_diagnostic_column(self):
        """Test that diagnostic column matches observed values."""
        sample_data = {
            "composition": [{"Fe": 0.5, "Ni": 0.5}],
            "Bulk_Modulus_Observed": [180.0]
        }
        df = pd.DataFrame(sample_data)
        
        result_df = compute_residual_target(df)
        
        assert np.isclose(
            result_df[DIAGNOSTIC_BULK_MODULUS_COL].iloc[0],
            result_df["Bulk_Modulus_Observed"].iloc[0]
        )