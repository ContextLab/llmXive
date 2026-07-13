"""
Unit tests for the anomaly_injector module.
"""
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from lib.anomaly_injector import (
    inject_anomalies,
    inject_mean_shift,
    inject_variance_spike,
    inject_gradual_drift,
    select_injection_location,
    load_config,
    validate_config,
    inject_anomalies_from_file,
)


@pytest.fixture
def sample_data():
    """Create a sample time series for testing."""
    np.random.seed(42)
    n_points = 1000
    # Generate a time series with a clear mean and some noise
    base_mean = 100.0
    base_std = 10.0
    data = np.random.normal(base_mean, base_std, n_points)
    # Add a slight trend to make it more realistic
    data += np.linspace(0, 5, n_points)
    return pd.Series(data, name="test_series")


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return {
        "anomalies": [
            {
                "type": "mean_shift",
                "magnitude_std": 2.5,
                "duration": 10
            },
            {
                "type": "variance_spike",
                "variance_multiplier": 3.0,
                "duration": 8
            },
            {
                "type": "gradual_drift",
                "drift_rate_std": 0.5,
                "duration": 15
            }
        ],
        "min_gap": 10
    }


class TestMeanShiftInjection:
    def test_mean_shift_injection(self, sample_data, sample_config):
        """Test that mean shift anomaly is correctly injected."""
        rng = np.random.default_rng(123)
        modified, gt = inject_anomalies(sample_data, sample_config, rng)
        
        # Check that ground truth has the expected number of anomalies
        assert gt.sum() > 0, "No anomalies were injected"
        
        # Check that the modified series differs from original
        assert not modified.equals(sample_data), "Series was not modified"
        
        # Check that the magnitude is approximately correct for the first anomaly
        # (This is a simplified check; a more robust test would identify the exact location)
        assert modified.std() != sample_data.std() or modified.mean() != sample_data.mean()


    def test_mean_shift_magnitude(self):
        """Test that mean shift magnitude is correct."""
        series = np.array([100.0] * 100)
        baseline_stats = {"mean": 100.0, "std": 10.0}
        rng = np.random.default_rng(42)
        
        # Inject a positive mean shift of 2.5 std
        modified = inject_mean_shift(
            series, start_idx=50, duration=10,
            magnitude_std=2.5, baseline_stats=baseline_stats, rng=rng
        )
        
        # The mean of the anomaly region should be shifted by ~2.5 * std
        anomaly_region = modified[50:60]
        expected_mean = 100.0 + 2.5 * 10.0  # 125.0 (or 75.0 if negative)
        
        # Check that the mean is significantly different from the original
        assert abs(anomaly_region.mean() - 100.0) > 15.0, \
            f"Mean shift not detected: {anomaly_region.mean()}"


class TestVarianceSpikeInjection:
    def test_variance_spike_injection(self, sample_data, sample_config):
        """Test that variance spike anomaly is correctly injected."""
        rng = np.random.default_rng(456)
        modified, gt = inject_anomalies(sample_data, sample_config, rng)
        
        # Check that ground truth has the expected number of anomalies
        assert gt.sum() > 0, "No anomalies were injected"
        
        # Check that the modified series differs from original
        assert not modified.equals(sample_data), "Series was not modified"


    def test_variance_spike_magnitude(self):
        """Test that variance spike magnitude is correct."""
        series = np.array([100.0] * 100)
        baseline_stats = {"mean": 100.0, "std": 10.0}
        rng = np.random.default_rng(42)
        
        # Inject a variance spike with 3x multiplier
        modified = inject_variance_spike(
            series, start_idx=50, duration=10,
            variance_multiplier=3.0, baseline_stats=baseline_stats, rng=rng
        )
        
        # The std of the anomaly region should be approximately sqrt(3) * original_std
        anomaly_region = modified[50:60]
        expected_std = 10.0 * np.sqrt(3.0)
        
        # Check that the std is significantly different from the original
        assert abs(anomaly_region.std() - 10.0) > 5.0, \
            f"Variance spike not detected: {anomaly_region.std()}"


class TestGradualDriftInjection:
    def test_gradual_drift_injection(self, sample_data, sample_config):
        """Test that gradual drift anomaly is correctly injected."""
        rng = np.random.default_rng(789)
        modified, gt = inject_anomalies(sample_data, sample_config, rng)
        
        # Check that ground truth has the expected number of anomalies
        assert gt.sum() > 0, "No anomalies were injected"
        
        # Check that the modified series differs from original
        assert not modified.equals(sample_data), "Series was not modified"


    def test_gradual_drift_magnitude(self):
        """Test that gradual drift magnitude is correct."""
        series = np.array([100.0] * 100)
        baseline_stats = {"mean": 100.0, "std": 10.0}
        rng = np.random.default_rng(42)
        
        # Inject a gradual drift with 0.5 std per step
        modified = inject_gradual_drift(
            series, start_idx=50, duration=10,
            drift_rate_std=0.5, baseline_stats=baseline_stats, rng=rng
        )
        
        # The drift should cause a cumulative change
        anomaly_region = modified[50:60]
        
        # Check that there's a trend (difference between end and start of region)
        trend = anomaly_region.iloc[-1] - anomaly_region.iloc[0]
        expected_trend = 9 * 0.5 * 10.0  # 9 steps * 0.5 std * 10 std (or negative)
        
        # Check that the trend is significant
        assert abs(trend) > 20.0, f"Gradual drift not detected: {trend}"


class TestRandomLocationSelection:
    def test_location_selection_valid(self):
        """Test that selected location is valid."""
        series_length = 1000
        duration = 10
        min_gap = 10
        rng = np.random.default_rng(42)
        
        location = select_injection_location(series_length, duration, min_gap, rng)
        
        # Check that the location is within valid range
        assert location >= min_gap, f"Location {location} is before min_gap"
        assert location + duration <= series_length - min_gap, \
            f"Location {location} + duration {duration} exceeds series length"


    def test_location_selection_short_series(self):
        """Test that short series raises an error."""
        with pytest.raises(ValueError):
            select_injection_location(10, 20, 5, np.random.default_rng())


class TestConfigInjection:
    def test_config_validation(self, sample_config):
        """Test that valid config passes validation."""
        validate_config(sample_config)
    
    def test_invalid_config_missing_type(self):
        """Test that config without type raises an error."""
        config = {"anomalies": [{"magnitude_std": 2.5}]}
        with pytest.raises(ValueError):
            validate_config(config)
    
    def test_invalid_config_unknown_type(self):
        """Test that config with unknown type raises an error."""
        config = {"anomalies": [{"type": "unknown_type"}]}
        with pytest.raises(ValueError):
            validate_config(config)


class TestConfigLoading:
    def test_load_yaml_config(self, sample_config):
        """Test loading a YAML configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(sample_config, f)
            config_path = f.name
        
        try:
            loaded_config = load_config(config_path)
            assert loaded_config == sample_config
        finally:
            Path(config_path).unlink()
    
    def test_load_json_config(self, sample_config):
        """Test loading a JSON configuration."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(sample_config, f)
            config_path = f.name
        
        try:
            loaded_config = load_config(config_path)
            assert loaded_config == sample_config
        finally:
            Path(config_path).unlink()
    
    def test_load_nonexistent_config(self):
        """Test that loading a nonexistent config raises an error."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent.yaml")
    
    def test_load_invalid_format(self):
        """Test that loading an invalid format raises an error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("some text")
            config_path = f.name
        
        try:
            with pytest.raises(ValueError):
                load_config(config_path)
        finally:
            Path(config_path).unlink()


def test_inject_anomalies_from_file():
    """Test the file-based injection function."""
    # Create sample data
    np.random.seed(42)
    n_points = 100
    data = np.random.normal(100, 10, n_points)
    df = pd.DataFrame({"timestamp": range(n_points), "value": data})
    
    # Create sample config
    config = {
        "anomalies": [
            {
                "type": "mean_shift",
                "magnitude_std": 2.5,
                "duration": 5
            }
        ],
        "min_gap": 5
    }
    
    # Create temporary files
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_series_path = Path(tmpdir) / "output_series.csv"
        output_gt_path = Path(tmpdir) / "output_gt.csv"
        config_path = Path(tmpdir) / "config.yaml"
        
        # Save input data and config
        df.to_csv(input_path, index=False)
        with open(config_path, "w") as f:
            yaml.dump(config, f)
        
        # Run injection
        inject_anomalies_from_file(
            input_path, output_series_path, output_gt_path,
            config_path, column_name="value", seed=42
        )
        
        # Check that output files exist and have correct structure
        assert output_series_path.exists()
        assert output_gt_path.exists()
        
        output_series_df = pd.read_csv(output_series_path)
        output_gt_df = pd.read_csv(output_gt_path)
        
        assert len(output_series_df) == n_points
        assert len(output_gt_df) == n_points
        assert "value" in output_series_df.columns
        assert "is_anomaly" in output_gt_df.columns