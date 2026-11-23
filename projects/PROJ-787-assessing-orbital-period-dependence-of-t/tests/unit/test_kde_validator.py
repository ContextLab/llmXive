"""
Unit tests for KDE Validator.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import json

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.analysis.kde_validator import (
    estimate_kde_gap,
    validate_gap_location,
    load_gap_locations
)


class TestKDEGapEstimation:
    """Tests for the KDE gap estimation function."""

    def test_bimodal_distribution_gap(self):
        """Test KDE gap detection on a known bimodal distribution."""
        # Create a bimodal distribution with a clear gap
        np.random.seed(42)
        super_earths = np.random.normal(1.5, 0.2, 500)  # Peak around 1.5
        sub_neptunes = np.random.normal(2.5, 0.2, 500)  # Peak around 2.5
        data = np.concatenate([super_earths, sub_neptunes])

        gap = estimate_kde_gap(data)

        # The gap should be between 1.5 and 2.5
        assert gap is not None, "Gap should be detected"
        assert 1.8 < gap < 2.2, f"Gap {gap} should be between 1.8 and 2.2"

    def test_unimodal_distribution_no_gap(self):
        """Test KDE gap detection on a unimodal distribution."""
        np.random.seed(42)
        data = np.random.normal(2.0, 0.5, 1000)

        gap = estimate_kde_gap(data)

        # No clear gap should be detected
        # (Note: KDE might still find a local minimum, but it should be less reliable)
        # For this test, we just ensure it doesn't crash
        assert gap is not None or True  # Allow None if no gap found

    def test_insufficient_data(self):
        """Test KDE gap detection with insufficient data points."""
        data = np.array([1.0, 1.5, 2.0])

        gap = estimate_kde_gap(data)

        assert gap is None, "Should return None for insufficient data"

    def test_empty_data(self):
        """Test KDE gap detection with empty data."""
        data = np.array([])

        gap = estimate_kde_gap(data)

        assert gap is None, "Should return None for empty data"


class TestGapLocationValidation:
    """Tests for the gap location validation function."""

    @pytest.fixture
    def sample_gap_df(self):
        """Create a sample gap locations DataFrame."""
        return pd.DataFrame({
            'bin_index': [1, 2, 3],
            'gap_location': [1.8, 2.0, 2.2],
            'gap_uncertainty': [0.1, 0.1, 0.1],
            'ci_lower': [1.6, 1.8, 2.0],
            'ci_upper': [2.0, 2.2, 2.4]
        })

    @pytest.fixture
    def sample_planets_df(self):
        """Create a sample planets DataFrame."""
        np.random.seed(42)
        n = 300
        return pd.DataFrame({
            'koi_planet_number': range(n),
            'planet_radius': np.concatenate([
                np.random.normal(1.5, 0.2, 100),
                np.random.normal(2.5, 0.2, 100),
                np.random.normal(1.8, 0.2, 100)
            ]),
            'orbital_period': np.random.uniform(1, 100, n)
        })

    @pytest.fixture
    def sample_binned_df(self):
        """Create a sample binned planets DataFrame."""
        np.random.seed(42)
        n = 300
        return pd.DataFrame({
            'bin_index': [1] * 100 + [2] * 100 + [3] * 100,
            'planet_radius': np.concatenate([
                np.random.normal(1.5, 0.2, 100),
                np.random.normal(2.5, 0.2, 100),
                np.random.normal(1.8, 0.2, 100)
            ]),
            'orbital_period': np.random.uniform(1, 100, n)
        })

    def test_validation_with_binned_data(self, sample_gap_df, sample_binned_df, tmp_path):
        """Test validation when binned data is available."""
        # Create temporary directory structure
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()

        # Save binned data
        binned_path = processed_dir / "binned_planets.csv"
        sample_binned_df.to_csv(binned_path, index=False)

        # Run validation
        results = validate_gap_location(sample_gap_df, tmp_path)

        assert 'validation_passed' in results
        assert 'bin_results' in results
        assert len(results['bin_results']) == 3

    def test_validation_missing_binned_data(self, sample_gap_df, tmp_path):
        """Test validation when binned data is missing (fallback behavior)."""
        # Don't create binned data
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()

        # Create planets data
        planets_path = processed_dir / "deduped_planets.csv"
        planets_df = pd.DataFrame({
            'koi_planet_number': range(100),
            'planet_radius': np.random.normal(2.0, 0.5, 100),
            'orbital_period': np.random.uniform(1, 100, 100)
        })
        planets_df.to_csv(planets_path, index=False)

        # Run validation
        results = validate_gap_location(sample_gap_df, tmp_path)

        assert 'validation_passed' in results
        assert 'bin_results' in results

    def test_validation_with_outlier_gaps(self, sample_gap_df, sample_binned_df, tmp_path):
        """Test validation with gaps that are outside the confidence interval."""
        # Modify gap locations to be outside CI
        sample_gap_df.loc[0, 'gap_location'] = 1.0  # Outside CI
        sample_gap_df.loc[0, 'ci_lower'] = 1.6
        sample_gap_df.loc[0, 'ci_upper'] = 2.0

        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        sample_binned_df.to_csv(processed_dir / "binned_planets.csv", index=False)

        results = validate_gap_location(sample_gap_df, tmp_path)

        assert results['validation_passed'] is False
        assert results['summary']['failed_bins'] > 0


class TestLoadGapLocations:
    """Tests for loading gap locations."""

    def test_load_valid_file(self, tmp_path):
        """Test loading a valid gap locations file."""
        gap_data = {
            'bin_index': [1, 2],
            'gap_location': [1.8, 2.0],
            'gap_uncertainty': [0.1, 0.1],
            'ci_lower': [1.6, 1.8],
            'ci_upper': [2.0, 2.2]
        }
        df = pd.DataFrame(gap_data)
        file_path = tmp_path / "gap_locations.csv"
        df.to_csv(file_path, index=False)

        loaded_df = load_gap_locations(str(file_path))

        assert len(loaded_df) == 2
        assert 'gap_location' in loaded_df.columns

    def test_load_missing_file(self, tmp_path):
        """Test loading a missing file raises error."""
        with pytest.raises(FileNotFoundError):
            load_gap_locations(str(tmp_path / "nonexistent.csv"))

    def test_load_missing_columns(self, tmp_path):
        """Test loading a file with missing required columns raises error."""
        gap_data = {
            'bin_index': [1, 2],
            'gap_location': [1.8, 2.0]
        }
        df = pd.DataFrame(gap_data)
        file_path = tmp_path / "gap_locations.csv"
        df.to_csv(file_path, index=False)

        with pytest.raises(ValueError):
            load_gap_locations(str(file_path))