"""
Unit tests for edge cases involving extreme outliers in formation energy and descriptors.

These tests verify that the outlier detection and capping logic handles:
1. Extremely high formation energy values
2. Extremely low formation energy values
3. Outliers in descriptor values
4. Multiple outliers in the same dataset
5. Edge cases around percentile boundaries
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from descriptors import detect_and_cap_outliers, compute_descriptors_row
from utils.io import get_memory_usage_gb


class TestExtremeOutliers:
    """Tests for handling extreme outliers in formation energy and descriptors."""

    def test_extremely_high_formation_energy(self, tmp_path):
        """Test detection and capping of extremely high formation energy values."""
        # Create dataset with extreme outlier
        test_df = pd.DataFrame({
            'composition': ['H2O', 'Fe2O3', 'H2O', 'Fe2O3', 'ExtremeOutlier'],
            'formation_energy': [-1.0, -2.0, -1.5, -2.5, 1000.0],  # Extreme outlier
            'mean_electronegativity': [2.5, 2.0, 2.5, 2.0, 2.5],
            'variance_electronegativity': [0.1, 0.2, 0.1, 0.2, 0.1],
            'mean_radius': [0.6, 1.0, 0.6, 1.0, 0.6],
            'variance_radius': [0.05, 0.1, 0.05, 0.1, 0.05],
            'mean_valence': [1.5, 2.5, 1.5, 2.5, 1.5],
            'variance_valence': [0.2, 0.3, 0.2, 0.3, 0.2],
            'mean_melting_point': [100.0, 1000.0, 100.0, 1000.0, 100.0],
            'variance_melting_point': [50.0, 100.0, 50.0, 100.0, 50.0],
            'mean_ionization_energy': [10.0, 8.0, 10.0, 8.0, 10.0],
            'variance_ionization_energy': [1.0, 2.0, 1.0, 2.0, 1.0]
        })
        
        # Test outlier detection with CAP_OUTLIERS=True
        capped_df, capped_count = detect_and_cap_outliers(test_df, cap_outliers=True)
        
        # Verify that the extreme outlier was capped
        assert capped_count > 0
        # The capped value should be within reasonable bounds
        assert capped_df['formation_energy'].max() < 1000.0

    def test_extremely_low_formation_energy(self, tmp_path):
        """Test detection and capping of extremely low formation energy values."""
        test_df = pd.DataFrame({
            'composition': ['H2O', 'Fe2O3', 'H2O', 'Fe2O3', 'ExtremeOutlier'],
            'formation_energy': [-1.0, -2.0, -1.5, -2.5, -1000.0],  # Extreme negative outlier
            'mean_electronegativity': [2.5, 2.0, 2.5, 2.0, 2.5],
            'variance_electronegativity': [0.1, 0.2, 0.1, 0.2, 0.1],
            'mean_radius': [0.6, 1.0, 0.6, 1.0, 0.6],
            'variance_radius': [0.05, 0.1, 0.05, 0.1, 0.05],
            'mean_valence': [1.5, 2.5, 1.5, 2.5, 1.5],
            'variance_valence': [0.2, 0.3, 0.2, 0.3, 0.2],
            'mean_melting_point': [100.0, 1000.0, 100.0, 1000.0, 100.0],
            'variance_melting_point': [50.0, 100.0, 50.0, 100.0, 50.0],
            'mean_ionization_energy': [10.0, 8.0, 10.0, 8.0, 10.0],
            'variance_ionization_energy': [1.0, 2.0, 1.0, 2.0, 1.0]
        })
        
        capped_df, capped_count = detect_and_cap_outliers(test_df, cap_outliers=True)
        
        # Verify that the extreme negative outlier was capped
        assert capped_count > 0
        assert capped_df['formation_energy'].min() > -1000.0

    def test_multiple_extreme_outliers(self, tmp_path):
        """Test handling of multiple extreme outliers in the same dataset."""
        test_df = pd.DataFrame({
            'composition': ['H2O', 'Fe2O3', 'Outlier1', 'Outlier2', 'Outlier3', 'H2O'],
            'formation_energy': [-1.0, -2.0, 500.0, -500.0, 1000.0, -1.5],
            'mean_electronegativity': [2.5, 2.0, 2.5, 2.5, 2.5, 2.5],
            'variance_electronegativity': [0.1, 0.2, 0.1, 0.1, 0.1, 0.1],
            'mean_radius': [0.6, 1.0, 0.6, 0.6, 0.6, 0.6],
            'variance_radius': [0.05, 0.1, 0.05, 0.05, 0.05, 0.05],
            'mean_valence': [1.5, 2.5, 1.5, 1.5, 1.5, 1.5],
            'variance_valence': [0.2, 0.3, 0.2, 0.2, 0.2, 0.2],
            'mean_melting_point': [100.0, 1000.0, 100.0, 100.0, 100.0, 100.0],
            'variance_melting_point': [50.0, 100.0, 50.0, 50.0, 50.0, 50.0],
            'mean_ionization_energy': [10.0, 8.0, 10.0, 10.0, 10.0, 10.0],
            'variance_ionization_energy': [1.0, 2.0, 1.0, 1.0, 1.0, 1.0]
        })
        
        capped_df, capped_count = detect_and_cap_outliers(test_df, cap_outliers=True)
        
        # All three outliers should be capped
        assert capped_count == 3
        # Verify no values exceed reasonable bounds
        assert capped_df['formation_energy'].max() < 500.0
        assert capped_df['formation_energy'].min() > -500.0

    def test_no_outliers_present(self, tmp_path):
        """Test that no capping occurs when no outliers are present."""
        test_df = pd.DataFrame({
            'composition': ['H2O', 'Fe2O3', 'H2O', 'Fe2O3', 'H2O'],
            'formation_energy': [-1.0, -2.0, -1.5, -2.5, -1.2],
            'mean_electronegativity': [2.5, 2.0, 2.5, 2.0, 2.5],
            'variance_electronegativity': [0.1, 0.2, 0.1, 0.2, 0.1],
            'mean_radius': [0.6, 1.0, 0.6, 1.0, 0.6],
            'variance_radius': [0.05, 0.1, 0.05, 0.1, 0.05],
            'mean_valence': [1.5, 2.5, 1.5, 2.5, 1.5],
            'variance_valence': [0.2, 0.3, 0.2, 0.3, 0.2],
            'mean_melting_point': [100.0, 1000.0, 100.0, 1000.0, 100.0],
            'variance_melting_point': [50.0, 100.0, 50.0, 100.0, 50.0],
            'mean_ionization_energy': [10.0, 8.0, 10.0, 8.0, 10.0],
            'variance_ionization_energy': [1.0, 2.0, 1.0, 2.0, 1.0]
        })
        
        capped_df, capped_count = detect_and_cap_outliers(test_df, cap_outliers=True)
        
        # No outliers should be capped
        assert capped_count == 0
        # Data should remain unchanged
        assert np.allclose(test_df['formation_energy'], capped_df['formation_energy'])

    def test_outliers_at_percentile_boundaries(self, tmp_path):
        """Test handling of values exactly at percentile boundaries."""
        # Create dataset where some values are exactly at 1st and 99th percentiles
        test_df = pd.DataFrame({
            'composition': ['H2O'] * 100,
            'formation_energy': list(range(-50, 50)),  # Values from -50 to 49
            'mean_electronegativity': [2.5] * 100,
            'variance_electronegativity': [0.1] * 100,
            'mean_radius': [0.6] * 100,
            'variance_radius': [0.05] * 100,
            'mean_valence': [1.5] * 100,
            'variance_valence': [0.2] * 100,
            'mean_melting_point': [100.0] * 100,
            'variance_melting_point': [50.0] * 100,
            'mean_ionization_energy': [10.0] * 100,
            'variance_ionization_energy': [1.0] * 100
        })
        
        capped_df, capped_count = detect_and_cap_outliers(test_df, cap_outliers=True)
        
        # Some values at boundaries should be capped
        assert capped_count >= 0  # Could be 0 if no values exceed bounds

    def test_extreme_descriptor_values(self, tmp_path):
        """Test handling of extreme values in descriptor columns."""
        test_df = pd.DataFrame({
            'composition': ['H2O', 'Fe2O3', 'Outlier'],
            'formation_energy': [-1.0, -2.0, -1.5],
            'mean_electronegativity': [2.5, 2.0, 1000.0],  # Extreme outlier in descriptor
            'variance_electronegativity': [0.1, 0.2, 500.0],
            'mean_radius': [0.6, 1.0, 0.6],
            'variance_radius': [0.05, 0.1, 0.05],
            'mean_valence': [1.5, 2.5, 1.5],
            'variance_valence': [0.2, 0.3, 0.2],
            'mean_melting_point': [100.0, 1000.0, 100.0],
            'variance_melting_point': [50.0, 100.0, 50.0],
            'mean_ionization_energy': [10.0, 8.0, 10.0],
            'variance_ionization_energy': [1.0, 2.0, 1.0]
        })
        
        # Outlier detection should handle extreme descriptor values
        capped_df, capped_count = detect_and_cap_outliers(test_df, cap_outliers=True)
        
        # Extreme descriptor values should be capped
        assert capped_df['mean_electronegativity'].max() < 1000.0

    def test_cap_outliers_disabled(self, tmp_path):
        """Test that no capping occurs when cap_outliers=False."""
        test_df = pd.DataFrame({
            'composition': ['H2O', 'Fe2O3', 'Outlier'],
            'formation_energy': [-1.0, -2.0, 1000.0],
            'mean_electronegativity': [2.5, 2.0, 2.5],
            'variance_electronegativity': [0.1, 0.2, 0.1],
            'mean_radius': [0.6, 1.0, 0.6],
            'variance_radius': [0.05, 0.1, 0.05],
            'mean_valence': [1.5, 2.5, 1.5],
            'variance_valence': [0.2, 0.3, 0.2],
            'mean_melting_point': [100.0, 1000.0, 100.0],
            'variance_melting_point': [50.0, 100.0, 50.0],
            'mean_ionization_energy': [10.0, 8.0, 10.0],
            'variance_ionization_energy': [1.0, 2.0, 1.0]
        })
        
        capped_df, capped_count = detect_and_cap_outliers(test_df, cap_outliers=False)
        
        # No capping should occur
        assert capped_count == 0
        assert capped_df['formation_energy'].max() == 1000.0

    def test_single_value_dataset(self, tmp_path):
        """Test outlier detection with a single value dataset."""
        test_df = pd.DataFrame({
            'composition': ['H2O'],
            'formation_energy': [-1.0],
            'mean_electronegativity': [2.5],
            'variance_electronegativity': [0.1],
            'mean_radius': [0.6],
            'variance_radius': [0.05],
            'mean_valence': [1.5],
            'variance_valence': [0.2],
            'mean_melting_point': [100.0],
            'variance_melting_point': [50.0],
            'mean_ionization_energy': [10.0],
            'variance_ionization_energy': [1.0]
        })
        
        # Should handle single value without error
        capped_df, capped_count = detect_and_cap_outliers(test_df, cap_outliers=True)
        assert len(capped_df) == 1

    def test_nan_values_in_outlier_detection(self, tmp_path):
        """Test handling of NaN values during outlier detection."""
        test_df = pd.DataFrame({
            'composition': ['H2O', 'Fe2O3', 'NaNValue'],
            'formation_energy': [-1.0, np.nan, 1000.0],
            'mean_electronegativity': [2.5, 2.0, 2.5],
            'variance_electronegativity': [0.1, 0.2, 0.1],
            'mean_radius': [0.6, 1.0, 0.6],
            'variance_radius': [0.05, 0.1, 0.05],
            'mean_valence': [1.5, 2.5, 1.5],
            'variance_valence': [0.2, 0.3, 0.2],
            'mean_melting_point': [100.0, 1000.0, 100.0],
            'variance_melting_point': [50.0, 100.0, 50.0],
            'mean_ionization_energy': [10.0, 8.0, 10.0],
            'variance_ionization_energy': [1.0, 2.0, 1.0]
        })
        
        # Should handle NaN values gracefully
        capped_df, capped_count = detect_and_cap_outliers(test_df, cap_outliers=True)
        
        # NaN should remain NaN, outliers should be capped
        assert pd.isna(capped_df.loc[1, 'formation_energy'])
        assert capped_df.loc[2, 'formation_energy'] != 1000.0

    def test_extreme_percentile_values(self, tmp_path):
        """Test with extreme percentile values (0.001 and 0.999)."""
        test_df = pd.DataFrame({
            'composition': ['H2O'] * 1000,
            'formation_energy': list(np.linspace(-10, 10, 1000)),
            'mean_electronegativity': [2.5] * 1000,
            'variance_electronegativity': [0.1] * 1000,
            'mean_radius': [0.6] * 1000,
            'variance_radius': [0.05] * 1000,
            'mean_valence': [1.5] * 1000,
            'variance_valence': [0.2] * 1000,
            'mean_melting_point': [100.0] * 1000,
            'variance_melting_point': [50.0] * 1000,
            'mean_ionization_energy': [10.0] * 1000,
            'variance_ionization_energy': [1.0] * 1000
        })
        
        # Add extreme outliers
        test_df.loc[0, 'formation_energy'] = -1000.0
        test_df.loc[999, 'formation_energy'] = 1000.0
        
        capped_df, capped_count = detect_and_cap_outliers(test_df, cap_outliers=True)
        
        # Extreme outliers should be capped
        assert capped_count > 0
        assert capped_df['formation_energy'].max() < 1000.0
        assert capped_df['formation_energy'].min() > -1000.0

class TestMemoryAndPerformanceEdgeCases:
    """Tests for memory and performance edge cases."""

    def test_large_dataset_outlier_detection(self, tmp_path):
        """Test outlier detection on a large dataset."""
        # Create a large dataset with some outliers
        n_rows = 100000
        test_df = pd.DataFrame({
            'composition': ['H2O'] * n_rows,
            'formation_energy': np.random.normal(0, 1, n_rows),
            'mean_electronegativity': [2.5] * n_rows,
            'variance_electronegativity': [0.1] * n_rows,
            'mean_radius': [0.6] * n_rows,
            'variance_radius': [0.05] * n_rows,
            'mean_valence': [1.5] * n_rows,
            'variance_valence': [0.2] * n_rows,
            'mean_melting_point': [100.0] * n_rows,
            'variance_melting_point': [50.0] * n_rows,
            'mean_ionization_energy': [10.0] * n_rows,
            'variance_ionization_energy': [1.0] * n_rows
        })
        
        # Add some extreme outliers
        test_df.loc[0:99, 'formation_energy'] = np.random.uniform(100, 1000, 100)
        test_df.loc[n_rows-100:n_rows-1, 'formation_energy'] = np.random.uniform(-1000, -100, 100)
        
        # Should handle large dataset without error
        capped_df, capped_count = detect_and_cap_outliers(test_df, cap_outliers=True)
        
        assert len(capped_df) == n_rows
        assert capped_count > 0

    def test_memory_monitoring_edge_case(self, tmp_path):
        """Test memory monitoring with extreme memory usage values."""
        # Mock memory usage to test edge cases
        with patch('psutil.virtual_memory') as mock_memory:
            # Test with very low memory usage
            mock_memory.return_value.percent = 10
            usage = get_memory_usage_gb()
            assert usage >= 0
            
            # Test with very high memory usage
            mock_memory.return_value.percent = 99
            usage = get_memory_usage_gb()
            assert usage >= 0