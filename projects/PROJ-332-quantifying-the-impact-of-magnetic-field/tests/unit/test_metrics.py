import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from analysis.metrics import calculate_resonant_surface_density, detect_outliers, validate_metric_ranges

class TestCalculateResonantSurfaceDensity:
    def test_no_rational_surfaces(self):
        """Test with q-profile that has no rational surfaces in range."""
        q = np.array([1.5, 1.6, 1.7, 1.8, 1.9])
        rho = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        density = calculate_resonant_surface_density(q, rho, m_min=2, m_max=4, n_min=1, n_max=2, tolerance=0.01)
        # Rational surfaces in range: 2/1=2, 3/1=3, 4/1=4, 2/2=1, 3/2=1.5, 4/2=2
        # q values are 1.5, 1.6, 1.7, 1.8, 1.9. Only 1.5 is close to 3/2=1.5
        # So we expect 1 rational surface. rho_range = 0.4. Density = 1/0.4 = 2.5
        assert abs(density - 2.5) < 0.01

    def test_empty_profile(self):
        """Test with empty q-profile."""
        q = np.array([])
        rho = np.array([])
        density = calculate_resonant_surface_density(q, rho)
        assert density == 0.0

    def test_all_nan_profile(self):
        """Test with all NaN values."""
        q = np.array([np.nan, np.nan, np.nan])
        rho = np.array([0.1, 0.2, 0.3])
        density = calculate_resonant_surface_density(q, rho)
        assert density == 0.0

    def test_single_rational_surface(self):
        """Test with exactly one rational surface."""
        # q = 2.0 exactly, which is 2/1, 4/2, etc.
        q = np.array([1.0, 2.0, 3.0])
        rho = np.array([0.0, 0.5, 1.0])
        density = calculate_resonant_surface_density(q, rho, m_min=2, m_max=4, n_min=1, n_max=2, tolerance=0.01)
        # Rational surfaces: 2/1=2, 3/1=3, 4/1=4, 2/2=1, 3/2=1.5, 4/2=2
        # q values: 1.0, 2.0, 3.0.
        # 1.0 matches 2/2 (1.0). 2.0 matches 2/1 (2.0) and 4/2 (2.0). 3.0 matches 3/1 (3.0).
        # Unique rational surfaces: 1.0, 2.0, 3.0 -> 3 surfaces.
        # rho_range = 1.0. Density = 3.0.
        assert abs(density - 3.0) < 0.01

    def test_tolerance_behavior(self):
        """Test that tolerance affects detection."""
        q = np.array([1.505])  # Close to 1.5 (3/2) but outside tolerance 0.01
        rho = np.array([0.5])
        density_strict = calculate_resonant_surface_density(q, rho, m_min=3, m_max=3, n_min=2, n_max=2, tolerance=0.001)
        density_loose = calculate_resonant_surface_density(q, rho, m_min=3, m_max=3, n_min=2, n_max=2, tolerance=0.01)
        # With strict tolerance, 1.505 is not close to 1.5 (diff 0.005 > 0.001) -> 0 surfaces
        # With loose tolerance, 1.505 is close to 1.5 (diff 0.005 < 0.01) -> 1 surface
        assert density_strict == 0.0
        assert density_loose > 0.0

class TestDetectOutliers:
    def test_no_outliers(self):
        """Test with no outliers."""
        df = pd.DataFrame({
            'discharge_id': [1, 2, 3],
            'island_width': [0.1, 0.2, 0.3],
            'minor_radius': [0.5, 0.6, 0.7]
        })
        outliers = detect_outliers(df)
        assert outliers == []

    def test_with_outliers(self):
        """Test with some outliers."""
        df = pd.DataFrame({
            'discharge_id': [1, 2, 3],
            'island_width': [0.1, 0.8, 0.3],
            'minor_radius': [0.5, 0.6, 0.7]
        })
        outliers = detect_outliers(df)
        assert 1 in outliers  # Row index 1 has 0.8 > 0.6

    def test_missing_columns(self):
        """Test with missing columns."""
        df = pd.DataFrame({
            'discharge_id': [1, 2, 3]
        })
        outliers = detect_outliers(df)
        assert outliers == []

class TestValidateMetricRanges:
    def test_valid_ranges(self):
        """Test with all metrics in valid range."""
        df = pd.DataFrame({
            'density': [1.0, 2.0, 3.0]
        })
        metrics = {'density': (0.0, 5.0)}
        assert validate_metric_ranges(df, metrics) is True

    def test_invalid_ranges(self):
        """Test with some metrics out of range."""
        df = pd.DataFrame({
            'density': [1.0, 6.0, 3.0]
        })
        metrics = {'density': (0.0, 5.0)}
        assert validate_metric_ranges(df, metrics) is False

    def test_missing_metric(self):
        """Test with missing metric column."""
        df = pd.DataFrame({
            'other_col': [1.0, 2.0]
        })
        metrics = {'density': (0.0, 5.0)}
        assert validate_metric_ranges(df, metrics) is False
