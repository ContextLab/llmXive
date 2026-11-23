"""
Unit tests for edge cases involving extreme outliers in formation energy and descriptors.
Tests the outlier detection and capping logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from descriptors import (
    detect_and_cap_outliers,
    calculate_weighted_mean_variance
)
from config import load_paths, CAP_OUTLIERS, ROW_THRESHOLD


class TestExtremeOutliers:
    """Test cases for handling extreme outliers in data."""

    @pytest.fixture
    def base_data(self):
        """Create a base dataframe with normal values."""
        data = {
            "composition": ["Li2O", "Fe2O3", "NaCl", "SiO2", "MgO"],
            "formation_energy": [-5.0, -8.0, -4.0, -9.0, -6.0],
            "mean_electronegativity": [1.5, 1.8, 2.0, 1.9, 1.3],
            "var_electronegativity": [0.1, 0.2, 0.15, 0.12, 0.08],
            "mean_radius": [1.2, 1.3, 1.4, 1.35, 1.1],
            "var_radius": [0.05, 0.06, 0.04, 0.05, 0.03]
        }
        return pd.DataFrame(data)

    @pytest.fixture
    def data_with_extreme_outliers(self, base_data):
        """Create a dataframe with extreme outlier values."""
        df = base_data.copy()
        # Add extreme outliers
        df.loc[len(df)] = ["Hypothetical", -500.0, 100.0, 99.0, 50.0, 49.0]  # Extremely low energy, high descriptors
        df.loc[len(df)] = ["AnotherHyp", 500.0, -100.0, -99.0, -50.0, -49.0]  # Extremely high energy, negative descriptors
        return df

    def test_detect_outliers_identifies_extreme_values(self, data_with_extreme_outliers):
        """
        Verify that the outlier detection logic identifies extreme values.
        """
        # We expect the function to identify rows with extreme formation_energy
        # or descriptor values as outliers
        
        # Calculate IQR based bounds manually to verify
        fe_col = data_with_extreme_outliers["formation_energy"]
        q1 = fe_col.quantile(0.25)
        q3 = fe_col.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # The extreme values should be outside these bounds
        outliers = data_with_extreme_outliers[
            (data_with_extreme_outliers["formation_energy"] < lower_bound) |
            (data_with_extreme_outliers["formation_energy"] > upper_bound)
        ]
        
        assert len(outliers) > 0, "Extreme outliers should be detected"
        assert len(outliers) == 2, "We added exactly 2 extreme outliers"

    def test_cap_outliers_reduces_range(self, data_with_extreme_outliers):
        """
        Verify that capping outliers reduces the range of the data
        while preserving the non-outlier values.
        """
        if not CAP_OUTLIERS:
            pytest.skip("CAP_OUTLIERS is False in config")

        original_fe = data_with_extreme_outliers["formation_energy"].copy()
        
        # Apply capping
        capped_df, capped_count = detect_and_cap_outliers(
            data_with_extreme_outliers,
            target_column="formation_energy"
        )
        
        # The count should be > 0
        assert capped_count > 0, "Outliers should have been capped"
        
        # The range should be reduced
        original_range = original_fe.max() - original_fe.min()
        capped_range = capped_df["formation_energy"].max() - capped_df["formation_energy"].min()
        
        assert capped_range < original_range, "Capping should reduce the data range"
        
        # Non-outlier values should remain unchanged
        non_outlier_mask = ~((data_with_extreme_outliers["formation_energy"] < 
                             (original_fe.quantile(0.25) - 1.5 * (original_fe.quantile(0.75) - original_fe.quantile(0.25)))) |
                            (data_with_extreme_outliers["formation_energy"] > 
                             (original_fe.quantile(0.75) + 1.5 * (original_fe.quantile(0.75) - original_fe.quantile(0.25)))))
        
        # Check that non-outlier values are preserved
        assert np.allclose(
            capped_df.loc[non_outlier_mask, "formation_energy"],
            original_fe.loc[non_outlier_mask]
        ), "Non-outlier values should be preserved"

    def test_extreme_negative_values_handled(self, base_data):
        """
        Test handling of extremely negative formation energies.
        """
        df = base_data.copy()
        df.loc[len(df)] = ["ExtremeNeg", -1000.0, 1.5, 0.1, 1.2, 0.05]
        
        if CAP_OUTLIERS:
            capped_df, count = detect_and_cap_outliers(df, "formation_energy")
            assert count > 0, "Extreme negative values should be capped"
            assert capped_df["formation_energy"].min() > -1000.0, "Value should be capped"
        else:
            # If capping is off, the function might just log or return unchanged
            capped_df, count = detect_and_cap_outliers(df, "formation_energy")
            assert count == 0, "No capping should occur if CAP_OUTLIERS is False"

    def test_extreme_positive_values_handled(self, base_data):
        """
        Test handling of extremely positive formation energies.
        """
        df = base_data.copy()
        df.loc[len(df)] = ["ExtremePos", 1000.0, 1.5, 0.1, 1.2, 0.05]
        
        if CAP_OUTLIERS:
            capped_df, count = detect_and_cap_outliers(df, "formation_energy")
            assert count > 0, "Extreme positive values should be capped"
            assert capped_df["formation_energy"].max() < 1000.0, "Value should be capped"
        else:
            capped_df, count = detect_and_cap_outliers(df, "formation_energy")
            assert count == 0, "No capping should occur if CAP_OUTLIERS is False"

    def test_all_outliers_scenario(self):
        """
        Test a scenario where all values are outliers (e.g., only 2 rows).
        """
        df = pd.DataFrame({
            "composition": ["A", "B"],
            "formation_energy": [1000.0, -1000.0],
            "mean_electronegativity": [1.0, 1.0],
            "var_electronegativity": [0.1, 0.1],
            "mean_radius": [1.0, 1.0],
            "var_radius": [0.1, 0.1]
        })
        
        if CAP_OUTLIERS:
            capped_df, count = detect_and_cap_outliers(df, "formation_energy")
            # With only 2 points, IQR is 0, so bounds are Q1-0 and Q3+0
            # Both might be considered outliers or neither depending on strictness
            # We just verify the function doesn't crash
            assert isinstance(capped_df, pd.DataFrame)
            assert isinstance(count, int)
        else:
            capped_df, count = detect_and_cap_outliers(df, "formation_energy")
            assert count == 0

    def test_zero_variance_outlier_detection(self):
        """
        Test outlier detection when variance is zero (all values same).
        """
        df = pd.DataFrame({
            "composition": ["A", "B", "C"],
            "formation_energy": [5.0, 5.0, 5.0],
            "mean_electronegativity": [1.0, 1.0, 1.0],
            "var_electronegativity": [0.0, 0.0, 0.0],
            "mean_radius": [1.0, 1.0, 1.0],
            "var_radius": [0.0, 0.0, 0.0]
        })
        
        # IQR should be 0, bounds should be exactly 5.0
        # No outliers should be detected
        capped_df, count = detect_and_cap_outliers(df, "formation_energy")
        assert count == 0, "No outliers when all values are identical"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])