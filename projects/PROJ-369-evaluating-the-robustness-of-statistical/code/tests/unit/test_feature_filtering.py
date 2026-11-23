"""
Unit tests for feature filtering logic (T037b).

Tests that Max_ACF_Lag and spectral density metrics are correctly excluded.
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.regression import filter_features, EXCLUDED_FEATURES, INCLUDED_FEATURES


class TestFeatureFiltering:
    """Test cases for feature filtering logic."""

    def test_excluded_features_defined(self):
        """Verify that excluded features are explicitly defined."""
        assert 'Max_ACF_Lag' in EXCLUDED_FEATURES
        assert 'spectral_density_peak_ratio' in EXCLUDED_FEATURES
        assert 'spectral_peak_ratio' in EXCLUDED_FEATURES

    def test_filter_removes_excluded_features(self):
        """Test that filter_features removes all excluded features."""
        test_features = [
            'hurst',
            'length',
            'Max_ACF_Lag',
            'spectral_density_peak_ratio',
            'variance',
            'spectral_peak_ratio'
        ]
        
        filtered = filter_features(test_features)
        
        # Verify excluded features are removed
        for excluded in EXCLUDED_FEATURES:
            assert excluded not in filtered, f"{excluded} should be filtered out"
        
        # Verify kept features remain
        assert 'hurst' in filtered
        assert 'length' in filtered
        assert 'variance' in filtered

    def test_filter_with_empty_list(self):
        """Test filtering an empty list."""
        filtered = filter_features([])
        assert filtered == []

    def test_filter_with_no_excluded_features(self):
        """Test filtering when no excluded features are present."""
        test_features = ['hurst', 'length', 'variance']
        filtered = filter_features(test_features)
        assert filtered == test_features

    def test_filter_preserves_order(self):
        """Test that filtering preserves the order of remaining features."""
        test_features = ['hurst', 'Max_ACF_Lag', 'length', 'spectral_peak_ratio', 'variance']
        filtered = filter_features(test_features)
        expected = ['hurst', 'length', 'variance']
        assert filtered == expected

    def test_all_known_features_filtered_correctly(self):
        """Test filtering with a comprehensive list of all known features."""
        all_features = [
            'hurst', 'length', 'acf_mean', 'acf_max', 'Max_ACF_Lag',
            'spectral_density_peak_ratio', 'spectral_peak_ratio',
            'variance', 'skewness', 'kurtosis', 'adf_statistic'
        ]
        
        filtered = filter_features(all_features)
        
        # Count should be total minus excluded
        expected_count = len(all_features) - len(EXCLUDED_FEATURES)
        assert len(filtered) == expected_count

    def test_excluded_features_list_is_complete(self):
        """Verify the excluded features list covers all spectral/ACF metrics."""
        # These are the features that should be excluded per T037b
        required_exclusions = ['Max_ACF_Lag', 'spectral_density_peak_ratio', 'spectral_peak_ratio']
        
        for feature in required_exclusions:
            assert feature in EXCLUDED_FEATURES, f"{feature} must be in EXCLUDED_FEATURES"