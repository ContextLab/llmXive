"""
Unit tests for edge cases involving extreme outliers in formation energy.

These tests verify that the outlier detection and capping logic correctly
handles extreme values without crashing and produces expected results.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from descriptors import detect_and_cap_outliers
from config import load_paths


class TestExtremeOutliers:
    """Tests for handling extreme outliers in formation energy."""

    @pytest.fixture
    def dataset_with_extreme_outliers(self):
        """Create a dataset with extreme outlier values."""
        np.random.seed(42)
        n_normal = 100
        
        # Normal data
        normal_energies = np.random.normal(-5.0, 2.0, n_normal)
        
        # Extreme outliers
        extreme_energies = np.array([
            -1000.0,  # Extreme negative outlier
            1000.0,   # Extreme positive outlier
            -5000.0,  # More extreme negative
            5000.0    # More extreme positive
        ])
        
        all_energies = np.concatenate([normal_energies, extreme_energies])
        
        data = {
            'formula': [f'Compound_{i}' for i in range(len(all_energies))],
            'formation_energy': all_energies,
            'mean_electronegativity': np.random.uniform(1.0, 4.0, len(all_energies)),
            'variance_radius': np.random.uniform(0.0, 1.0, len(all_energies)),
            'mean_valence': np.random.uniform(1.0, 8.0, len(all_energies)),
            'mean_melting_point': np.random.uniform(300.0, 3000.0, len(all_energies)),
            'mean_ionization_energy': np.random.uniform(3.0, 15.0, len(all_energies))
        }
        return pd.DataFrame(data)

    def test_detect_and_cap_outliers_normal_data(self, dataset_with_extreme_outliers):
        """Test outlier detection on data with extreme values."""
        # Run outlier detection
        capped_df, capped_count = detect_and_cap_outliers(
            dataset_with_extreme_outliers, 
            cap_outliers=True
        )
        
        # Should have capped some values
        assert capped_count > 0, "Expected some outliers to be capped"
        
        # Check that extreme values are now within bounds
        # The exact bounds depend on the percentiles calculated from the data
        min_energy = capped_df['formation_energy'].min()
        max_energy = capped_df['formation_energy'].max()
        
        # Extreme outliers should be capped, so min/max should be reasonable
        # relative to the normal distribution
        assert min_energy > -100.0, "Extreme negative outliers should be capped"
        assert max_energy < 100.0, "Extreme positive outliers should be capped"

    def test_detect_and_cap_outliers_disabled(self, dataset_with_extreme_outliers):
        """Test that outliers are NOT capped when cap_outliers=False."""
        capped_df, capped_count = detect_and_cap_outliers(
            dataset_with_extreme_outliers, 
            cap_outliers=False
        )
        
        # No capping should occur
        assert capped_count == 0, "Expected no outliers to be capped when disabled"
        
        # Original extreme values should remain
        assert -1000.0 in capped_df['formation_energy'].values, \
            "Extreme negative outlier should remain uncapped"
        assert 1000.0 in capped_df['formation_energy'].values, \
            "Extreme positive outlier should remain uncapped"

    def test_capped_values_at_boundaries(self, dataset_with_extreme_outliers):
        """Test that capped values are exactly at the percentile boundaries."""
        capped_df, _ = detect_and_cap_outliers(
            dataset_with_extreme_outliers, 
            cap_outliers=True
        )
        
        # Calculate the percentile boundaries that should have been used
        energies = dataset_with_extreme_outliers['formation_energy']
        lower_bound = np.percentile(energies, 1)
        upper_bound = np.percentile(energies, 99)
        
        # Check that no values are below lower_bound or above upper_bound
        assert capped_df['formation_energy'].min() >= lower_bound - 1e-6, \
            "Values should not be below the lower percentile bound"
        assert capped_df['formation_energy'].max() <= upper_bound + 1e-6, \
            "Values should not be above the upper percentile bound"

    def test_all_outliers_dataset(self):
        """Test handling of a dataset where ALL values are outliers."""
        # Create a dataset where every value is an extreme outlier
        data = {
            'formula': ['Outlier1', 'Outlier2', 'Outlier3', 'Outlier4'],
            'formation_energy': [-10000.0, -5000.0, 5000.0, 10000.0],
            'mean_electronegativity': [1.0, 2.0, 3.0, 4.0],
            'variance_radius': [0.1, 0.2, 0.3, 0.4],
            'mean_valence': [1.0, 2.0, 3.0, 4.0],
            'mean_melting_point': [300.0, 600.0, 900.0, 1200.0],
            'mean_ionization_energy': [3.0, 6.0, 9.0, 12.0]
        }
        df = pd.DataFrame(data)
        
        capped_df, capped_count = detect_and_cap_outliers(df, cap_outliers=True)
        
        # All values should be capped
        assert capped_count == 4, "All values should be capped in extreme dataset"
        
        # Values should be at the boundaries
        energies = capped_df['formation_energy']
        assert energies.min() == energies.max(), \
            "All values should be capped to the same boundary in extreme case"

    def test_single_value_dataset(self):
        """Test handling of a dataset with only one value."""
        data = {
            'formula': ['Single'],
            'formation_energy': [-5.0],
            'mean_electronegativity': [2.0],
            'variance_radius': [0.5],
            'mean_valence': [3.0],
            'mean_melting_point': [1000.0],
            'mean_ionization_energy': [7.0]
        }
        df = pd.DataFrame(data)
        
        # Should not crash with single value
        capped_df, capped_count = detect_and_cap_outliers(df, cap_outliers=True)
        
        assert len(capped_df) == 1, "Should return single row"
        assert capped_count == 0, "No outliers in single-value dataset"

    def test_nan_in_outlier_detection(self):
        """Test handling of NaN values in outlier detection."""
        data = {
            'formula': ['Normal', 'NaN_Value', 'Outlier'],
            'formation_energy': [-5.0, np.nan, 1000.0],
            'mean_electronegativity': [2.0, 3.0, 4.0],
            'variance_radius': [0.5, 0.6, 0.7],
            'mean_valence': [3.0, 4.0, 5.0],
            'mean_melting_point': [1000.0, 1100.0, 1200.0],
            'mean_ionization_energy': [7.0, 8.0, 9.0]
        }
        df = pd.DataFrame(data)
        
        # Should not crash with NaN values
        try:
            capped_df, capped_count = detect_and_cap_outliers(df, cap_outliers=True)
            # NaN should remain NaN, outlier should be capped
            assert pd.isna(capped_df.loc[1, 'formation_energy']), \
                "NaN values should remain NaN"
        except Exception as e:
            # If it raises, that's also acceptable behavior for NaN handling
            # The important thing is it doesn't crash silently or produce wrong results
            assert "NaN" in str(e) or "null" in str(e).lower(), \
                f"Error message should mention NaN handling: {e}"

    def test_extreme_percentiles(self):
        """Test with extreme percentile thresholds (1st and 99th)."""
        # Create dataset with known distribution
        np.random.seed(42)
        normal = np.random.normal(-5.0, 1.0, 1000)
        outliers = np.array([-50.0, 50.0])
        data = np.concatenate([normal, outliers])
        
        df = pd.DataFrame({
            'formula': [f'Comp_{i}' for i in range(len(data))],
            'formation_energy': data,
            'mean_electronegativity': np.random.uniform(1, 4, len(data)),
            'variance_radius': np.random.uniform(0, 1, len(data)),
            'mean_valence': np.random.uniform(1, 8, len(data)),
            'mean_melting_point': np.random.uniform(300, 3000, len(data)),
            'mean_ionization_energy': np.random.uniform(3, 15, len(data))
        })
        
        capped_df, capped_count = detect_and_cap_outliers(df, cap_outliers=True)
        
        # Should have capped the extreme values
        assert capped_count > 0, "Expected outliers to be capped"
        
        # Check bounds
        assert capped_df['formation_energy'].min() > -20.0, \
            "Extreme negative values should be capped"
        assert capped_df['formation_energy'].max() < 20.0, \
            "Extreme positive values should be capped"
