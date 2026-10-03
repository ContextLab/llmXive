"""
Tests for the anomaly injector library.

Author: Research Team
Date: 2026-04-29
"""

import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from lib.anomaly_injector import (
    inject_mean_shift,
    inject_variance_spike,
    inject_gradual_drift,
    select_anomaly_locations,
    inject_anomalies,
    load_config,
    inject_anomalies_from_file
)


@pytest.fixture
def sample_data():
    """Create a sample time series for testing."""
    np.random.seed(42)
    return np.random.normal(0, 1, 1000)


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return {
        "anomalies": [
            {
                "type": "mean_shift",
                "shift_magnitude": 2.5,
                "duration_range": [5, 15],
                "min_gap": 10
            },
            {
                "type": "variance_spike",
                "variance_multiplier": 3.0,
                "duration_range": [5, 15],
                "min_gap": 10
            }
        ],
        "min_gap": 10
    }


class TestMeanShiftInjection:
    """Tests for mean shift anomaly injection."""

    def test_mean_shift_increases_values(self, sample_data):
        """Test that mean shift increases values by the specified amount."""
        start_idx, end_idx = 100, 110
        shift_magnitude = 2.5
        std_dev = np.std(sample_data)
        expected_shift = shift_magnitude * std_dev

        result = inject_mean_shift(sample_data, start_idx, end_idx, shift_magnitude, seed=42)

        # Check that the shifted segment has increased mean
        original_mean = np.mean(sample_data[start_idx:end_idx])
        shifted_mean = np.mean(result[start_idx:end_idx])
        
        assert abs(shifted_mean - (original_mean + expected_shift)) < 0.01

    def test_mean_shift_preserves_other_values(self, sample_data):
        """Test that mean shift only affects the specified segment."""
        start_idx, end_idx = 100, 110
        shift_magnitude = 2.5

        result = inject_mean_shift(sample_data, start_idx, end_idx, shift_magnitude, seed=42)

        # Check that non-shifted segments are unchanged
        np.testing.assert_array_equal(result[:start_idx], sample_data[:start_idx])
        np.testing.assert_array_equal(result[end_idx:], sample_data[end_idx:])


class TestVarianceSpikeInjection:
    """Tests for variance spike anomaly injection."""

    def test_variance_spike_increases_variance(self, sample_data):
        """Test that variance spike increases variance by the specified multiplier."""
        start_idx, end_idx = 100, 110
        variance_multiplier = 3.0

        result = inject_variance_spike(sample_data, start_idx, end_idx, variance_multiplier, seed=42)

        # Check that the variance of the shifted segment has increased
        original_segment = sample_data[start_idx:end_idx]
        shifted_segment = result[start_idx:end_idx]
        
        original_var = np.var(original_segment)
        shifted_var = np.var(shifted_segment)
        
        # The variance should be approximately multiplied by the multiplier
        assert shifted_var > original_var * 2  # Allow some tolerance due to randomness

    def test_variance_spike_preserves_other_values(self, sample_data):
        """Test that variance spike only affects the specified segment."""
        start_idx, end_idx = 100, 110
        variance_multiplier = 3.0

        result = inject_variance_spike(sample_data, start_idx, end_idx, variance_multiplier, seed=42)

        # Check that non-shifted segments are unchanged
        np.testing.assert_array_equal(result[:start_idx], sample_data[:start_idx])
        np.testing.assert_array_equal(result[end_idx:], sample_data[end_idx:])


class TestGradualDriftInjection:
    """Tests for gradual drift anomaly injection."""

    def test_gradual_drift_adds_linear_trend(self, sample_data):
        """Test that gradual drift adds a linear trend to the specified segment."""
        start_idx, end_idx = 100, 110
        drift_rate = 0.1

        result = inject_gradual_drift(sample_data, start_idx, end_idx, drift_rate, seed=42)

        # Check that the segment has a linear trend
        shifted_segment = result[start_idx:end_idx]
        expected_drift = np.linspace(0, drift_rate * (end_idx - start_idx), end_idx - start_idx)
        
        # The difference should be approximately the drift
        diff = shifted_segment - sample_data[start_idx:end_idx]
        np.testing.assert_array_almost_equal(diff, expected_drift, decimal=5)

    def test_gradual_drift_preserves_other_values(self, sample_data):
        """Test that gradual drift only affects the specified segment."""
        start_idx, end_idx = 100, 110
        drift_rate = 0.1

        result = inject_gradual_drift(sample_data, start_idx, end_idx, drift_rate, seed=42)

        # Check that non-shifted segments are unchanged
        np.testing.assert_array_equal(result[:start_idx], sample_data[:start_idx])
        np.testing.assert_array_equal(result[end_idx:], sample_data[end_idx:])


class TestRandomLocationSelection:
    """Tests for random anomaly location selection."""

    def test_locations_within_bounds(self, sample_data, sample_config):
        """Test that selected locations are within the series bounds."""
        locations = select_anomaly_locations(
            len(sample_data), 
            sample_config['anomalies'], 
            sample_config['min_gap'], 
            seed=42
        )

        for start_idx, end_idx, _, _ in locations:
            assert 0 <= start_idx < len(sample_data)
            assert 0 < end_idx <= len(sample_data)
            assert start_idx < end_idx

    def test_no_overlapping_locations(self, sample_data, sample_config):
        """Test that selected locations do not overlap."""
        locations = select_anomaly_locations(
            len(sample_data), 
            sample_config['anomalies'], 
            sample_config['min_gap'], 
            seed=42
        )

        for i in range(len(locations)):
            for j in range(i + 1, len(locations)):
                start1, end1, _, _ = locations[i]
                start2, end2, _, _ = locations[j]
                
                # Check for no overlap
                assert end1 <= start2 or end2 <= start1


class TestConfigInjection:
    """Tests for configuration-based anomaly injection."""

    def test_inject_anomalies_from_config(self, sample_data, sample_config):
        """Test that anomalies are injected according to the configuration."""
        locations = select_anomaly_locations(
            len(sample_data), 
            sample_config['anomalies'], 
            sample_config['min_gap'], 
            seed=42
        )
        
        result, ground_truth = inject_anomalies(sample_data, locations, seed=42)

        # Check that ground truth has the expected number of anomalies
        assert len(ground_truth) == len(locations)

        # Check that the result has anomalies
        assert not np.array_equal(result, sample_data)


class TestConfigLoading:
    """Tests for configuration loading."""

    def test_load_json_config(self, sample_config):
        """Test loading a JSON configuration file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config, f)
            config_path = Path(f.name)

        try:
            config = load_config(config_path)
            assert config == sample_config
        finally:
            config_path.unlink()

    def test_load_yaml_config(self, sample_config):
        """Test loading a YAML configuration file."""
        import yaml
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(sample_config, f)
            config_path = Path(f.name)

        try:
            config = load_config(config_path)
            assert config == sample_config
        finally:
            config_path.unlink()

    def test_missing_config_file(self):
        """Test that an error is raised for a missing config file."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("nonexistent_config.json"))


def test_inject_anomalies_from_file():
    """Test the full pipeline of injecting anomalies from files."""
    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create sample data
        data_path = tmpdir / "series.csv"
        df = pd.DataFrame({'value': np.random.normal(0, 1, 1000)})
        df.to_csv(data_path, index=False)

        # Create sample config
        config_path = tmpdir / "config.json"
        config = {
            "anomalies": [
                {
                    "type": "mean_shift",
                    "shift_magnitude": 2.5,
                    "duration_range": [5, 15],
                    "min_gap": 10
                }
            ],
            "min_gap": 10
        }
        with open(config_path, 'w') as f:
            json.dump(config, f)

        # Output paths
        output_path = tmpdir / "series_with_anomalies.csv"
        ground_truth_path = tmpdir / "ground_truth.csv"

        # Run injection
        df_anomaly, df_ground_truth = inject_anomalies_from_file(
            data_path=data_path,
            config_path=config_path,
            output_path=output_path,
            ground_truth_path=ground_truth_path,
            seed=42
        )

        # Check outputs
        assert output_path.exists()
        assert ground_truth_path.exists()
        assert len(df_ground_truth) > 0
        assert 'is_anomaly' in df_ground_truth.columns