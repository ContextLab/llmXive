"""
Unit tests for outlier detection and capping logic.

These tests verify the percentile-based outlier detection and capping
functionality with various edge cases.
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


class TestOutlierDetection:
    """Tests for outlier detection and capping."""

    @pytest.fixture
    def normal_distribution_data(self):
        """Create a dataset with normally distributed formation energies."""
        np.random.seed(42)
        energies = np.random.normal(-5.0, 2.0, 1000)
        
        data = {
            'formula': [f'Compound_{i}' for i in range(len(energies))],
            'formation_energy': energies,
            'mean_electronegativity': np.random.uniform(1.0, 4.0, len(energies)),
            'variance_radius': np.random.uniform(0.0, 1.0, len(energies)),
            'mean_valence': np.random.uniform(1.0, 8.0, len(energies)),
            'mean_melting_point': np.random.uniform(300.0, 3000.0, len(energies)),
            'mean_ionization_energy': np.random.uniform(3.0, 15.0, len(energies))
        }
        return pd.DataFrame(data)

    def test_outlier_detection_with_normal_data(self, normal_distribution_data):
        """Test outlier detection on normally distributed data."""
        capped_df, capped_count = detect_and_cap_outliers(
            normal_distribution_data, cap_outliers=True
        )
        
        # With 1000 normal samples, there should be few or no outliers
        # (depending on the percentile thresholds)
        assert capped_count >= 0, "Capped count should be non-negative"
        assert len(capped_df) == len(normal_distribution_data), \
            "Number of rows should remain the same"

    def test_outlier_detection_with_no_outliers(self):
        """Test outlier detection on data with no outliers."""
        # Create data within a tight range
        energies = np.linspace(-6.0, -4.0, 100)
        
        data = {
            'formula': [f'Compound_{i}' for i in range(len(energies))],
            'formation_energy': energies,
            'mean_electronegativity': np.ones(len(energies)) * 2.0,
            'variance_radius': np.ones(len(energies)) * 0.5,
            'mean_valence': np.ones(len(energies)) * 3.0,
            'mean_melting_point': np.ones(len(energies)) * 1000.0,
            'mean_ionization_energy': np.ones(len(energies)) * 7.0
        }
        df = pd.DataFrame(data)
        
        capped_df, capped_count = detect_and_cap_outliers(df, cap_outliers=True)
        
        # No outliers should be capped
        assert capped_count == 0, "No outliers should be capped in tight distribution"

    def test_outlier_detection_with_single_outlier(self):
        """Test outlier detection with a single extreme outlier."""
        np.random.seed(42)
        normal = np.random.normal(-5.0, 1.0, 100)
        outlier = np.array([1000.0])
        energies = np.concatenate([normal, outlier])
        
        data = {
            'formula': [f'Compound_{i}' for i in range(len(energies))],
            'formation_energy': energies,
            'mean_electronegativity': np.random.uniform(1.0, 4.0, len(energies)),
            'variance_radius': np.random.uniform(0.0, 1.0, len(energies)),
            'mean_valence': np.random.uniform(1.0, 8.0, len(energies)),
            'mean_melting_point': np.random.uniform(300.0, 3000.0, len(energies)),
            'mean_ionization_energy': np.random.uniform(3.0, 15.0, len(energies))
        }
        df = pd.DataFrame(data)
        
        capped_df, capped_count = detect_and_cap_outliers(df, cap_outliers=True)
        
        # The outlier should be capped
        assert capped_count >= 1, "At least one outlier should be capped"
        
        # Check that the outlier value is now within bounds
        assert capped_df['formation_energy'].max() < 1000.0, \
            "Extreme outlier should be capped"

    def test_outlier_detection_with_multiple_outliers(self):
        """Test outlier detection with multiple outliers."""
        np.random.seed(42)
        normal = np.random.normal(-5.0, 1.0, 100)
        outliers = np.array([-100.0, 100.0, -200.0, 200.0])
        energies = np.concatenate([normal, outliers])
        
        data = {
            'formula': [f'Compound_{i}' for i in range(len(energies))],
            'formation_energy': energies,
            'mean_electronegativity': np.random.uniform(1.0, 4.0, len(energies)),
            'variance_radius': np.random.uniform(0.0, 1.0, len(energies)),
            'mean_valence': np.random.uniform(1.0, 8.0, len(energies)),
            'mean_melting_point': np.random.uniform(300.0, 3000.0, len(energies)),
            'mean_ionization_energy': np.random.uniform(3.0, 15.0, len(energies))
        }
        df = pd.DataFrame(data)
        
        capped_df, capped_count = detect_and_cap_outliers(df, cap_outliers=True)
        
        # Multiple outliers should be capped
        assert capped_count >= 4, "Multiple outliers should be capped"

    def test_outlier_detection_disabled(self, normal_distribution_data):
        """Test that outlier detection can be disabled."""
        capped_df, capped_count = detect_and_cap_outliers(
            normal_distribution_data, cap_outliers=False
        )
        
        # No capping should occur
        assert capped_count == 0, "No outliers should be capped when disabled"
        
        # Original values should be preserved
        pd.testing.assert_series_equal(
            capped_df['formation_energy'],
            normal_distribution_data['formation_energy']
        )

    def test_outlier_detection_percentile_bounds(self, normal_distribution_data):
        """Test that capped values are at the correct percentile bounds."""
        capped_df, _ = detect_and_cap_outliers(
            normal_distribution_data, cap_outliers=True
        )
        
        # Calculate the percentile bounds that should have been used
        energies = normal_distribution_data['formation_energy']
        lower_bound = np.percentile(energies, 1)
        upper_bound = np.percentile(energies, 99)
        
        # Check that no values are below lower_bound or above upper_bound
        assert capped_df['formation_energy'].min() >= lower_bound - 1e-6, \
            "Values should not be below the lower percentile bound"
        assert capped_df['formation_energy'].max() <= upper_bound + 1e-6, \
            "Values should not be above the upper percentile bound"

    def test_outlier_detection_with_small_dataset(self):
        """Test outlier detection with a very small dataset."""
        data = {
            'formula': ['A', 'B', 'C', 'D', 'E'],
            'formation_energy': [-5.0, -6.0, -7.0, -4.0, -8.0],
            'mean_electronegativity': [2.0, 2.1, 2.2, 1.9, 2.3],
            'variance_radius': [0.5, 0.5, 0.5, 0.5, 0.5],
            'mean_valence': [3.0, 3.0, 3.0, 3.0, 3.0],
            'mean_melting_point': [1000.0, 1000.0, 1000.0, 1000.0, 1000.0],
            'mean_ionization_energy': [7.0, 7.0, 7.0, 7.0, 7.0]
        }
        df = pd.DataFrame(data)
        
        # Should not crash with small dataset
        capped_df, capped_count = detect_and_cap_outliers(df, cap_outliers=True)
        
        assert len(capped_df) == len(df), "Row count should be preserved"

    def test_outlier_detection_with_two_values(self):
        """Test outlier detection with only two values."""
        data = {
            'formula': ['A', 'B'],
            'formation_energy': [-5.0, -6.0],
            'mean_electronegativity': [2.0, 2.1],
            'variance_radius': [0.5, 0.5],
            'mean_valence': [3.0, 3.0],
            'mean_melting_point': [1000.0, 1000.0],
            'mean_ionization_energy': [7.0, 7.0]
        }
        df = pd.DataFrame(data)
        
        # Should not crash with two values
        capped_df, capped_count = detect_and_cap_outliers(df, cap_outliers=True)
        
        assert len(capped_df) == len(df), "Row count should be preserved"

    def test_outlier_detection_with_one_value(self):
        """Test outlier detection with only one value."""
        data = {
            'formula': ['A'],
            'formation_energy': [-5.0],
            'mean_electronegativity': [2.0],
            'variance_radius': [0.5],
            'mean_valence': [3.0],
            'mean_melting_point': [1000.0],
            'mean_ionization_energy': [7.0]
        }
        df = pd.DataFrame(data)
        
        # Should not crash with one value
        capped_df, capped_count = detect_and_cap_outliers(df, cap_outliers=True)
        
        assert len(capped_df) == len(df), "Row count should be preserved"
        assert capped_count == 0, "No outliers in single-value dataset"

    def test_outlier_detection_preserves_other_columns(self, normal_distribution_data):
        """Test that outlier detection preserves non-energy columns."""
        capped_df, _ = detect_and_cap_outliers(
            normal_distribution_data, cap_outliers=True
        )
        
        # Check that other columns are preserved
        for col in ['formula', 'mean_electronegativity', 'variance_radius',
                    'mean_valence', 'mean_melting_point', 'mean_ionization_energy']:
            pd.testing.assert_series_equal(
                capped_df[col],
                normal_distribution_data[col],
                obj=f"Column {col} should be preserved"
            )

    def test_outlier_detection_with_negative_percentiles(self):
        """Test that the function handles negative formation energies correctly."""
        # Create data with all negative values
        energies = np.random.normal(-10.0, 2.0, 100)
        
        data = {
            'formula': [f'Compound_{i}' for i in range(len(energies))],
            'formation_energy': energies,
            'mean_electronegativity': np.random.uniform(1.0, 4.0, len(energies)),
            'variance_radius': np.random.uniform(0.0, 1.0, len(energies)),
            'mean_valence': np.random.uniform(1.0, 8.0, len(energies)),
            'mean_melting_point': np.random.uniform(300.0, 3000.0, len(energies)),
            'mean_ionization_energy': np.random.uniform(3.0, 15.0, len(energies))
        }
        df = pd.DataFrame(data)
        
        capped_df, capped_count = detect_and_cap_outliers(df, cap_outliers=True)
        
        # Should handle negative values correctly
        assert len(capped_df) == len(df), "Row count should be preserved"
        assert capped_df['formation_energy'].min() >= df['formation_energy'].quantile(0.01) - 1e-6

    def test_outlier_detection_with_positive_percentiles(self):
        """Test that the function handles positive formation energies correctly."""
        # Create data with some positive values (unusual but possible)
        energies = np.random.normal(5.0, 2.0, 100)
        
        data = {
            'formula': [f'Compound_{i}' for i in range(len(energies))],
            'formation_energy': energies,
            'mean_electronegativity': np.random.uniform(1.0, 4.0, len(energies)),
            'variance_radius': np.random.uniform(0.0, 1.0, len(energies)),
            'mean_valence': np.random.uniform(1.0, 8.0, len(energies)),
            'mean_melting_point': np.random.uniform(300.0, 3000.0, len(energies)),
            'mean_ionization_energy': np.random.uniform(3.0, 15.0, len(energies))
        }
        df = pd.DataFrame(data)
        
        capped_df, capped_count = detect_and_cap_outliers(df, cap_outliers=True)
        
        # Should handle positive values correctly
        assert len(capped_df) == len(df), "Row count should be preserved"