"""
Unit tests for target calculation module (src/features/targets.py).
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.features.targets import compute_residual_target, calculate_miedema_bulk_modulus

class TestTargetCalculation:
    """Tests for target calculation logic."""

    def test_compute_residual_target_basic(self):
        """Test basic residual calculation."""
        # Create a mock DataFrame with required columns
        data = {
            'Bulk_Modulus_Observed': [150.0, 200.0, 180.0],
            'mixing_enthalpy_miedema': [-10.0, -5.0, -8.0],
            'electronegativity_variance_miedema': [0.1, 0.2, 0.15],
            'atomic_radius_variance_miedema': [0.05, 0.03, 0.04]
        }
        df = pd.DataFrame(data)

        result_df = compute_residual_target(df, observed_col='Bulk_Modulus_Observed')

        # Check that new columns exist
        assert 'Bulk_Modulus_Miedema' in result_df.columns
        assert 'Bulk_Modulus_Residual' in result_df.columns

        # Check calculation: Residual = Observed - Miedema
        # We can't verify exact Miedema values without the exact formula,
        # but we can verify the relationship holds.
        expected_residual = result_df['Bulk_Modulus_Observed'] - result_df['Bulk_Modulus_Miedema']
        pd.testing.assert_series_equal(result_df['Bulk_Modulus_Residual'], expected_residual)

    def test_compute_residual_target_missing_observed(self):
        """Test that missing observed column raises error."""
        df = pd.DataFrame({'other_col': [1, 2, 3]})
        
        with pytest.raises(ValueError, match="Observed Bulk Modulus column"):
            compute_residual_target(df, observed_col='Bulk_Modulus_Observed')

    def test_compute_residual_target_missing_miedema_features(self):
        """Test that missing Miedema features raise error."""
        data = {
            'Bulk_Modulus_Observed': [150.0],
            'some_other_col': [1.0]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="Missing required Miedema features"):
            compute_residual_target(df)

    def test_miedema_bulk_modulus_calculation(self):
        """Test the Miedema bulk modulus calculation function directly."""
        data = {
            'mixing_enthalpy_miedema': [-10.0],
            'electronegativity_variance_miedema': [0.1],
            'atomic_radius_variance_miedema': [0.05]
        }
        df = pd.DataFrame(data)
        
        b_miedema = calculate_miedema_bulk_modulus(df)
        
        # Verify it returns a pandas Series
        assert isinstance(b_miedema, pd.Series)
        assert len(b_miedema) == 1
        
        # Verify the calculation logic (using the placeholder formula from targets.py)
        # B = 150 - 5*(-10) - 20*(0.1) + 10*(0.05)
        # B = 150 + 50 - 2 + 0.5 = 198.5
        expected_val = 150.0 - 5.0 * (-10.0) - 20.0 * (0.1) + 10.0 * (0.05)
        assert np.isclose(b_miedema.iloc[0], expected_val)

    def test_residual_with_nan(self):
        """Test handling of NaN values in observed data."""
        data = {
            'Bulk_Modulus_Observed': [150.0, np.nan, 180.0],
            'mixing_enthalpy_miedema': [-10.0, -5.0, -8.0],
            'electronegativity_variance_miedema': [0.1, 0.2, 0.15],
            'atomic_radius_variance_miedema': [0.05, 0.03, 0.04]
        }
        df = pd.DataFrame(data)
        
        result_df = compute_residual_target(df)
        
        # Check that NaN propagates correctly
        assert pd.isna(result_df.loc[1, 'Bulk_Modulus_Residual'])
        assert not pd.isna(result_df.loc[0, 'Bulk_Modulus_Residual'])
        assert not pd.isna(result_df.loc[2, 'Bulk_Modulus_Residual'])