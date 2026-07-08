"""
Tests for the anomaly injector library.
"""
import pytest
import numpy as np
import tempfile
import os
from pathlib import Path

from lib.anomaly_injector import (
    inject_mean_shift,
    inject_variance_spike,
    inject_gradual_drift,
    select_random_anomaly_location,
    inject_anomalies_from_config,
    load_config
)


@pytest.fixture
def sample_data():
    """Generate sample time series data for testing."""
    np.random.seed(42)
    return np.random.normal(0, 1, 1000)


@pytest.fixture
def sample_config():
    """Generate sample configuration for testing."""
    return {
        "anomaly_type": "mean_shift",
        "min_duration": 5,
        "max_duration": 15,
        "shift_magnitude": 2.5,
        "buffer_from_edges": 10
    }


class TestMeanShiftInjection:
    """Tests for mean shift anomaly injection."""

    def test_mean_shift_basic(self, sample_data):
        """Test basic mean shift injection."""
        std_dev = np.std(sample_data)
        modified_data, metadata = inject_mean_shift(
            sample_data, 100, 110, 2.5, std_dev, seed=42
        )

        # Check that data was modified
        assert not np.array_equal(modified_data, sample_data)

        # Check that only the specified segment was modified
        assert np.array_equal(modified_data[:100], sample_data[:100])
        assert np.array_equal(modified_data[111:], sample_data[111:])

        # Check metadata
        assert metadata["type"] == "mean_shift"
        assert metadata["start_idx"] == 100
        assert metadata["end_idx"] == 110
        assert metadata["shift_magnitude"] == 2.5

    def test_mean_shift_invalid_indices(self, sample_data):
        """Test mean shift with invalid indices."""
        std_dev = np.std(sample_data)

        with pytest.raises(ValueError):
            inject_mean_shift(sample_data, -1, 10, 2.5, std_dev)

        with pytest.raises(ValueError):
            inject_mean_shift(sample_data, 100, 1100, 2.5, std_dev)

        with pytest.raises(ValueError):
            inject_mean_shift(sample_data, 110, 100, 2.5, std_dev)


class TestVarianceSpikeInjection:
    """Tests for variance spike anomaly injection."""

    def test_variance_spike_basic(self, sample_data):
        """Test basic variance spike injection."""
        modified_data, metadata = inject_variance_spike(
            sample_data, 100, 110, 3.0, seed=42
        )

        # Check that data was modified
        assert not np.array_equal(modified_data, sample_data)

        # Check metadata
        assert metadata["type"] == "variance_spike"
        assert metadata["variance_multiplier"] == 3.0

    def test_variance_spike_invalid_multiplier(self, sample_data):
        """Test variance spike with invalid multiplier."""
        with pytest.raises(ValueError):
            inject_variance_spike(sample_data, 100, 110, -1.0)

        with pytest.raises(ValueError):
            inject_variance_spike(sample_data, 100, 110, 0.0)


class TestGradualDriftInjection:
    """Tests for gradual drift anomaly injection."""

    def test_gradual_drift_basic(self, sample_data):
        """Test basic gradual drift injection."""
        std_dev = np.std(sample_data)
        modified_data, metadata = inject_gradual_drift(
            sample_data, 100, 110, 2.0, std_dev, seed=42
        )

        # Check that data was modified
        assert not np.array_equal(modified_data, sample_data)

        # Check metadata
        assert metadata["type"] == "gradual_drift"
        assert metadata["drift_magnitude"] == 2.0

    def test_gradual_drift_invalid_indices(self, sample_data):
        """Test gradual drift with invalid indices."""
        std_dev = np.std(sample_data)

        with pytest.raises(ValueError):
            inject_gradual_drift(sample_data, -1, 10, 2.0, std_dev)

        with pytest.raises(ValueError):
            inject_gradual_drift(sample_data, 100, 1100, 2.0, std_dev)


class TestRandomLocationSelection:
    """Tests for random anomaly location selection."""

    def test_random_location_valid(self):
        """Test random location selection with valid parameters."""
        start, end = select_random_anomaly_location(1000, 5, 15, 10)

        assert start >= 10
        assert end < 990
        assert end - start + 1 >= 5
        assert end - start + 1 <= 15

    def test_random_location_invalid_duration(self):
        """Test random location selection with invalid duration."""
        with pytest.raises(ValueError):
            select_random_anomaly_location(100, 50, 60, 10)

    def test_random_location_invalid_indices(self):
        """Test random location selection with invalid indices."""
        with pytest.raises(ValueError):
            select_random_anomaly_location(1000, 1000, 2000, 10)


class TestConfigInjection:
    """Tests for configuration-based anomaly injection."""

    def test_config_mean_shift(self, sample_data, sample_config):
        """Test config-based mean shift injection."""
        modified_data, metadata_list = inject_anomalies_from_config(
            sample_data, sample_config, seed=42
        )

        assert not np.array_equal(modified_data, sample_data)
        assert len(metadata_list) == 1
        assert metadata_list[0]["type"] == "mean_shift"

    def test_config_variance_spike(self, sample_data):
        """Test config-based variance spike injection."""
        config = {
            "anomaly_type": "variance_spike",
            "min_duration": 5,
            "max_duration": 15,
            "variance_multiplier": 3.0,
            "buffer_from_edges": 10
        }

        modified_data, metadata_list = inject_anomalies_from_config(
            sample_data, config, seed=42
        )

        assert not np.array_equal(modified_data, sample_data)
        assert len(metadata_list) == 1
        assert metadata_list[0]["type"] == "variance_spike"

    def test_config_gradual_drift(self, sample_data):
        """Test config-based gradual drift injection."""
        std_dev = np.std(sample_data)
        config = {
            "anomaly_type": "gradual_drift",
            "min_duration": 5,
            "max_duration": 15,
            "drift_magnitude": 2.0,
            "buffer_from_edges": 10
        }

        modified_data, metadata_list = inject_anomalies_from_config(
            sample_data, config, seed=42
        )

        assert not np.array_equal(modified_data, sample_data)
        assert len(metadata_list) == 1
        assert metadata_list[0]["type"] == "gradual_drift"

    def test_config_unknown_type(self, sample_data):
        """Test config with unknown anomaly type."""
        config = {
            "anomaly_type": "unknown_type",
            "min_duration": 5,
            "max_duration": 15,
            "buffer_from_edges": 10
        }

        with pytest.raises(ValueError):
            inject_anomalies_from_config(sample_data, config, seed=42)


class TestConfigLoading:
    """Tests for configuration loading."""

    def test_load_yaml_config(self, sample_config):
        """Test loading YAML configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(sample_config, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config == sample_config
        finally:
            os.unlink(temp_path)

    def test_load_json_config(self, sample_config):
        """Test loading JSON configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(sample_config, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config == sample_config
        finally:
            os.unlink(temp_path)

    def test_load_nonexistent_config(self):
        """Test loading non-existent configuration."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.yaml")

    def test_load_invalid_format(self):
        """Test loading invalid format configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("invalid content")
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_config(temp_path)
        finally:
            os.unlink(temp_path)
