import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from physics import validate_derived_columns, calculate_quiescent_xuv, calculate_cumulative_flux, calculate_retention_fraction

class TestValidateDerivedColumns:
    """Tests for T026: Validation logic to ensure no NaN values in derived columns."""

    def test_valid_data_no_nans(self):
        """Test that valid data with no NaNs passes validation."""
        df = pd.DataFrame({
            'cumulative_flux': [1.0, 2.0, 3.0],
            'mass_loss_rate': [1e10, 2e10, 3e10],
            'retention_fraction': [0.9, 0.8, 0.7]
        })
        
        result_df, is_valid = validate_derived_columns(df)
        
        assert is_valid is True
        assert len(result_df) == 3
        assert result_df['cumulative_flux'].isna().sum() == 0
        assert result_df['mass_loss_rate'].isna().sum() == 0
        assert result_df['retention_fraction'].isna().sum() == 0

    def test_invalid_data_with_nans_raises_error(self):
        """Test that data with NaN values in derived columns raises ValueError."""
        df = pd.DataFrame({
            'cumulative_flux': [1.0, np.nan, 3.0],
            'mass_loss_rate': [1e10, 2e10, 3e10],
            'retention_fraction': [0.9, 0.8, 0.7]
        })
        
        with pytest.raises(ValueError, match="NaN values found in derived columns"):
            validate_derived_columns(df)

    def test_missing_derived_column_raises_error(self):
        """Test that missing derived columns raise ValueError."""
        df = pd.DataFrame({
            'cumulative_flux': [1.0, 2.0, 3.0],
            'mass_loss_rate': [1e10, 2e10, 3e10]
            # retention_fraction missing
        })
        
        with pytest.raises(ValueError, match="Missing derived columns for validation"):
            validate_derived_columns(df)

    def test_all_nans_in_column_raises_error(self):
        """Test that all NaNs in a derived column raises error."""
        df = pd.DataFrame({
            'cumulative_flux': [np.nan, np.nan, np.nan],
            'mass_loss_rate': [1e10, 2e10, 3e10],
            'retention_fraction': [0.9, 0.8, 0.7]
        })
        
        with pytest.raises(ValueError, match="NaN values found in derived columns"):
            validate_derived_columns(df)

    def test_edge_case_zero_values_pass(self):
        """Test that zero values (not NaN) pass validation."""
        df = pd.DataFrame({
            'cumulative_flux': [0.0, 1.0, 2.0],
            'mass_loss_rate': [0.0, 1e10, 2e10],
            'retention_fraction': [0.0, 0.5, 1.0]
        })
        
        result_df, is_valid = validate_derived_columns(df)
        
        assert is_valid is True
        assert (result_df['cumulative_flux'] == 0.0).sum() == 1

    def test_integration_with_physics_pipeline(self):
        """
        Integration test: Ensure the full physics pipeline 
        produces valid output (no NaNs) when run on valid input.
        This simulates the T025 -> T026 flow.
        """
        # Create a minimal valid input dataframe
        input_data = {
            'host_star_id': [1, 2, 3],
            'L_X': [1e27, 2e27, 3e27],
            'semi_major_axis': [0.1, 0.2, 0.3],
            'total_flare_energy': [1e30, 2e30, 3e30],
            'radius': [1.0, 1.5, 2.0],
            'mass': [1.0, 1.2, 1.5],
            'system_age': [5.0, 4.0, 3.0]
        }
        df_input = pd.DataFrame(input_data)
        
        # Run physics steps manually to ensure no NaNs are introduced
        df = calculate_quiescent_xuv(df_input.copy())
        df = calculate_cumulative_flux(df)
        df = calculate_retention_fraction(df)
        
        # Now run the T026 validation
        try:
            df_validated, is_valid = validate_derived_columns(df)
            assert is_valid is True
        except ValueError as e:
            pytest.fail(f"Physics pipeline introduced NaN values: {e}")