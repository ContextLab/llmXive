"""
Unit tests for data injection schema and anomaly injection logic.
Validates that injected anomalies match expected parameters and ground truth.
"""
import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path
from lib.anomaly_injector import (
    load_config,
    inject_mean_shift,
    inject_variance_spike,
    inject_gradual_drift,
    select_random_anomaly_location,
    inject_anomalies_from_config,
    main
)
from lib.metrics import precision_recall_f1

class TestMeanShiftInjection:
    def test_mean_shift_applied(self):
        """Verify mean shift injects the correct magnitude."""
        np.random.seed(42)
        data = np.random.normal(loc=0.0, scale=1.0, size=100)
        start, length = 40, 10
        shift_magnitude = 2.5  # 2.5 sigma as per FR-009
        
        injected, gt = inject_mean_shift(data, start, length, shift_magnitude)
        
        # Check ground truth
        assert len(gt) == len(data)
        assert np.sum(gt) == length
        assert np.all(gt[start:start+length] == 1)
        assert np.all(gt[:start] == 0)
        assert np.all(gt[start+length:] == 0)
        
        # Check injection magnitude
        injected_segment = injected[start:start+length]
        expected_mean = shift_magnitude
        actual_mean = np.mean(injected_segment)
        # Allow small tolerance for floating point
        assert abs(actual_mean - expected_mean) < 0.1

    def test_no_look_ahead_bias(self):
        """Ensure injection doesn't modify data before the anomaly window."""
        np.random.seed(123)
        original_data = np.random.normal(0, 1, 100)
        data_copy = original_data.copy()
        
        injected, _ = inject_mean_shift(data_copy, 50, 5, 3.0)
        
        # Pre-anomaly data should be identical
        assert np.array_equal(injected[:50], original_data[:50])

class TestVarianceSpikeInjection:
    def test_variance_spike_applied(self):
        """Verify variance spike increases variance by factor of 3 (FR-009)."""
        np.random.seed(42)
        data = np.random.normal(loc=0.0, scale=1.0, size=100)
        start, length = 40, 10
        variance_multiplier = 3.0
        
        injected, gt = inject_variance_spike(data, start, length, variance_multiplier)
        
        # Check ground truth
        assert len(gt) == len(data)
        assert np.sum(gt) == length
        
        # Check variance increase (approximate due to randomness)
        baseline_var = np.var(data[:start])
        spike_var = np.var(injected[start:start+length])
        # Variance should be roughly 3x baseline, allow 2x-5x range for stochasticity
        assert 2.0 * baseline_var < spike_var < 5.0 * baseline_var

class TestGradualDriftInjection:
    def test_gradual_drift_direction(self):
        """Verify gradual drift moves in the specified direction."""
        np.random.seed(42)
        data = np.zeros(100)
        start, length = 40, 20
        drift_magnitude = 1.0  # Total drift over the window
        
        injected, gt = inject_gradual_drift(data, start, length, drift_magnitude)
        
        segment = injected[start:start+length]
        # Drift should be monotonic increasing
        assert np.all(np.diff(segment) >= -1e-6)  # Allow tiny floating point errors
        # End value should be close to drift_magnitude
        assert abs(segment[-1] - drift_magnitude) < 0.1

class TestRandomLocationSelection:
    def test_location_bounds(self):
        """Ensure selected location is within valid bounds."""
        data = np.random.normal(0, 1, 100)
        min_len, max_len = 5, 15
        
        start, length = select_random_anomaly_location(data, min_len, max_len, seed=42)
        
        assert 0 <= start
        assert start + length <= len(data)
        assert min_len <= length <= max_len

    def test_no_overlap_with_existing(self):
        """Ensure new anomaly doesn't overlap with existing anomalies."""
        data = np.zeros(100)
        existing_gt = np.zeros(100)
        existing_gt[20:25] = 1  # Existing anomaly at 20-25
        
        min_len, max_len = 5, 10
        start, length = select_random_anomaly_location(
            data, min_len, max_len, existing_gt=existing_gt, seed=42
        )
        
        # Check no overlap
        new_anomaly_mask = np.zeros(100)
        new_anomaly_mask[start:start+length] = 1
        assert np.sum(existing_gt & new_anomaly_mask) == 0

class TestConfigInjection:
    def test_config_loading(self):
        """Verify config file loads correctly."""
        config = {
            "anomalies": [
                {
                    "type": "mean_shift",
                    "magnitude": 2.5,
                    "min_length": 5,
                    "max_length": 15,
                    "count": 1
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(config, f)
            temp_path = f.name
        
        try:
            loaded = load_config(temp_path)
            assert len(loaded['anomalies']) == 1
            assert loaded['anomalies'][0]['type'] == 'mean_shift'
        finally:
            os.unlink(temp_path)

    def test_full_injection_pipeline(self):
        """Test end-to-end injection from config."""
        np.random.seed(42)
        data = np.random.normal(0, 1, 200)
        
        config = {
            "anomalies": [
                {
                    "type": "mean_shift",
                    "magnitude": 2.5,
                    "min_length": 5,
                    "max_length": 10,
                    "count": 1
                },
                {
                    "type": "variance_spike",
                    "multiplier": 3.0,
                    "min_length": 5,
                    "max_length": 10,
                    "count": 1
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            import yaml
            yaml.dump(config, f)
            temp_path = f.name
        
        try:
            injected, ground_truth = inject_anomalies_from_config(data, temp_path, seed=42)
            
            # Verify output dimensions
            assert len(injected) == len(data)
            assert len(ground_truth) == len(data)
            
            # Verify at least some anomalies were injected
            assert np.sum(ground_truth) > 0
            
            # Verify injected data differs from original where anomalies exist
            anomaly_indices = np.where(ground_truth == 1)[0]
            assert len(anomaly_indices) > 0
            assert not np.array_equal(injected[anomaly_indices], data[anomaly_indices])
        finally:
            os.unlink(temp_path)

class TestSchemaValidation:
    def test_ground_truth_format(self):
        """Verify ground truth is binary and same length as data."""
        np.random.seed(42)
        data = np.random.normal(0, 1, 100)
        
        injected, gt = inject_mean_shift(data, 40, 10, 2.5)
        
        assert isinstance(gt, np.ndarray)
        assert gt.dtype in [np.int64, np.int32, np.float64]
        assert len(gt) == len(data)
        assert np.all(np.isin(gt, [0, 1]))

    def test_output_consistency(self):
        """Ensure injected and ground truth arrays are consistent."""
        np.random.seed(42)
        data = np.random.normal(0, 1, 100)
        
        injected, gt = inject_anomalies_from_config(
            data, 
            config_path=None,  # Will use default config
            seed=42
        )
        
        # Both should be numpy arrays
        assert isinstance(injected, np.ndarray)
        assert isinstance(gt, np.ndarray)
        
        # Both should have same length
        assert len(injected) == len(gt) == len(data)

def test_main_entry_point():
    """Test that main() runs without error (integration check)."""
    # Create a temporary config file
    config = {
        "anomalies": [
            {
                "type": "mean_shift",
                "magnitude": 2.5,
                "min_length": 5,
                "max_length": 10,
                "count": 1
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(config, f)
        config_path = f.name
    
    try:
        # Create a temporary data file
        data = np.random.normal(0, 1, 100)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            pd.DataFrame({'value': data}).to_csv(f, index=False)
            data_path = f.name
        
        with tempfile.TemporaryDirectory() as out_dir:
            output_prefix = Path(out_dir) / "test_output"
            
            # Run main
            main(
                data_path=data_path,
                config_path=config_path,
                output_prefix=str(output_prefix),
                seed=42
            )
            
            # Verify outputs exist
            assert (Path(out_dir) / "test_output_injected.csv").exists()
            assert (Path(out_dir) / "test_output_ground_truth.csv").exists()
    finally:
        os.unlink(config_path)
        if 'data_path' in locals():
            os.unlink(data_path)
