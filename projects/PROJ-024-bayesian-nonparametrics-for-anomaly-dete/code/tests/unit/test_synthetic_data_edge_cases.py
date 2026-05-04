"""
Unit tests for synthetic data generator edge cases.

Tests cover:
- Edge case anomaly injection
- Extreme parameter values
- Empty/invalid inputs
- Memory edge cases
"""
import pytest
import numpy as np
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.data.synthetic_generator import (
    AnomalyConfig, SignalConfig, SyntheticDataset,
    generate_base_signal, inject_point_anomalies,
    inject_contextual_anomalies, inject_collective_anomalies,
    generate_synthetic_timeseries
)


class TestSyntheticDataEdgeCases:
    """Test synthetic data generator edge cases."""
    
    def test_zero_length_signal(self):
        """Test generating zero-length signal."""
        config = SignalConfig(
            length=0,
            noise_level=0.1,
            frequency=1.0
        )
        
        signal = generate_base_signal(config)
        assert len(signal) == 0
    
    def test_very_short_signal(self):
        """Test generating very short signal."""
        config = SignalConfig(
            length=2,
            noise_level=0.1,
            frequency=1.0
        )
        
        signal = generate_base_signal(config)
        assert len(signal) == 2
    
    def test_very_long_signal(self):
        """Test generating very long signal."""
        config = SignalConfig(
            length=100000,
            noise_level=0.1,
            frequency=1.0
        )
        
        signal = generate_base_signal(config)
        assert len(signal) == 100000
    
    def test_zero_noise_level(self):
        """Test with zero noise."""
        config = SignalConfig(
            length=100,
            noise_level=0.0,
            frequency=1.0
        )
        
        signal = generate_base_signal(config)
        # Should be deterministic
        signal2 = generate_base_signal(config)
        np.testing.assert_array_equal(signal, signal2)
    
    def test_very_high_noise(self):
        """Test with extremely high noise."""
        config = SignalConfig(
            length=100,
            noise_level=1000.0,
            frequency=1.0
        )
        
        signal = generate_base_signal(config)
        assert len(signal) == 100
        # Should not crash, just very noisy
        assert np.std(signal) > 100.0
    
    def test_zero_frequency(self):
        """Test with zero frequency (constant signal)."""
        config = SignalConfig(
            length=100,
            noise_level=0.1,
            frequency=0.0
        )
        
        signal = generate_base_signal(config)
        # Should be mostly constant (just noise)
        assert len(signal) == 100
    
    def test_negative_frequency(self):
        """Test with negative frequency."""
        config = SignalConfig(
            length=100,
            noise_level=0.1,
            frequency=-1.0
        )
        
        signal = generate_base_signal(config)
        assert len(signal) == 100
    
    def test_anomaly_config_zero_probability(self):
        """Test anomaly injection with zero probability."""
        signal = np.sin(np.linspace(0, 10, 100))
        
        anomaly_config = AnomalyConfig(
            anomaly_probability=0.0,
            anomaly_magnitude=5.0,
            anomaly_duration=5
        )
        
        anomalous_signal, anomaly_labels = inject_point_anomalies(
            signal, anomaly_config, random_seed=42
        )
        
        # Should have no anomalies
        assert np.sum(anomaly_labels) == 0
        np.testing.assert_array_equal(signal, anomalous_signal)
    
    def test_anomaly_config_probability_one(self):
        """Test anomaly injection with probability 1."""
        signal = np.sin(np.linspace(0, 10, 100))
        
        anomaly_config = AnomalyConfig(
            anomaly_probability=1.0,
            anomaly_magnitude=5.0,
            anomaly_duration=1
        )
        
        anomalous_signal, anomaly_labels = inject_point_anomalies(
            signal, anomaly_config, random_seed=42
        )
        
        # Should have many anomalies
        assert np.sum(anomaly_labels) > 50
    
    def test_anomaly_magnitude_zero(self):
        """Test anomaly injection with zero magnitude."""
        signal = np.sin(np.linspace(0, 10, 100))
        
        anomaly_config = AnomalyConfig(
            anomaly_probability=0.5,
            anomaly_magnitude=0.0,
            anomaly_duration=1
        )
        
        anomalous_signal, anomaly_labels = inject_point_anomalies(
            signal, anomaly_config, random_seed=42
        )
        
        # Should have anomaly labels but no actual changes
        assert np.sum(anomaly_labels) > 0
        np.testing.assert_array_equal(signal, anomalous_signal)
    
    def test_anomaly_duration_exceeds_signal(self):
        """Test anomaly duration longer than signal."""
        signal = np.sin(np.linspace(0, 10, 10))  # Only 10 points
        
        anomaly_config = AnomalyConfig(
            anomaly_probability=1.0,
            anomaly_magnitude=5.0,
            anomaly_duration=100  # Longer than signal
        )
        
        # Should handle gracefully
        anomalous_signal, anomaly_labels = inject_point_anomalies(
            signal, anomaly_config, random_seed=42
        )
        assert len(anomalous_signal) == 10
        assert len(anomaly_labels) == 10
    
    def test_empty_anomaly_injection(self):
        """Test anomaly injection on empty signal."""
        signal = np.array([])
        
        anomaly_config = AnomalyConfig(
            anomaly_probability=0.5,
            anomaly_magnitude=5.0,
            anomaly_duration=5
        )
        
        anomalous_signal, anomaly_labels = inject_point_anomalies(
            signal, anomaly_config, random_seed=42
        )
        assert len(anomalous_signal) == 0
        assert len(anomaly_labels) == 0
    
    def test_collective_anomaly_edge_cases(self):
        """Test collective anomaly injection edge cases."""
        signal = np.sin(np.linspace(0, 10, 100))
        
        anomaly_config = AnomalyConfig(
            anomaly_probability=0.1,
            anomaly_magnitude=5.0,
            anomaly_duration=50  # Long duration collective anomaly
        )
        
        anomalous_signal, anomaly_labels = inject_collective_anomalies(
            signal, anomaly_config, random_seed=42
        )
        assert len(anomalous_signal) == 100
        assert len(anomaly_labels) == 100
    
    def test_contextual_anomaly_edge_cases(self):
        """Test contextual anomaly injection edge cases."""
        signal = np.sin(np.linspace(0, 10, 100))
        
        anomaly_config = AnomalyConfig(
            anomaly_probability=0.2,
            anomaly_magnitude=3.0,
            anomaly_duration=1
        )
        
        anomalous_signal, anomaly_labels = inject_contextual_anomalies(
            signal, anomaly_config, random_seed=42
        )
        assert len(anomalous_signal) == 100
        assert len(anomaly_labels) == 100
    
    def test_generate_synthetic_timeseries_minimal(self):
        """Test minimal synthetic timeseries generation."""
        signal_config = SignalConfig(
            length=10,
            noise_level=0.1,
            frequency=1.0
        )
        anomaly_config = AnomalyConfig(
            anomaly_probability=0.1,
            anomaly_magnitude=5.0,
            anomaly_duration=3
        )
        
        dataset = generate_synthetic_timeseries(
            signal_config, anomaly_config, random_seed=42
        )
        
        assert len(dataset.signal) == 10
        assert len(dataset.anomaly_labels) == 10
        assert dataset.anomaly_labels.sum() >= 0
    
    def test_generate_synthetic_timeseries_multivariate(self):
        """Test multivariate synthetic timeseries."""
        signal_config = SignalConfig(
            length=100,
            noise_level=0.1,
            frequency=1.0,
            n_features=3
        )
        anomaly_config = AnomalyConfig(
            anomaly_probability=0.1,
            anomaly_magnitude=5.0,
            anomaly_duration=3
        )
        
        dataset = generate_synthetic_timeseries(
            signal_config, anomaly_config, random_seed=42
        )
        
        assert dataset.signal.shape == (100, 3)
        assert dataset.anomaly_labels.shape == (100,)
    
    def test_generate_synthetic_timeseries_no_anomalies(self):
        """Test synthetic timeseries with no anomalies."""
        signal_config = SignalConfig(
            length=100,
            noise_level=0.1,
            frequency=1.0
        )
        anomaly_config = AnomalyConfig(
            anomaly_probability=0.0,
            anomaly_magnitude=5.0,
            anomaly_duration=3
        )
        
        dataset = generate_synthetic_timeseries(
            signal_config, anomaly_config, random_seed=42
        )
        
        assert np.sum(dataset.anomaly_labels) == 0
    
    def test_random_seed_reproducibility(self):
        """Test that random seed produces reproducible results."""
        signal_config = SignalConfig(
            length=100,
            noise_level=0.1,
            frequency=1.0
        )
        anomaly_config = AnomalyConfig(
            anomaly_probability=0.1,
            anomaly_magnitude=5.0,
            anomaly_duration=3
        )
        
        dataset1 = generate_synthetic_timeseries(
            signal_config, anomaly_config, random_seed=42
        )
        dataset2 = generate_synthetic_timeseries(
            signal_config, anomaly_config, random_seed=42
        )
        
        np.testing.assert_array_equal(dataset1.signal, dataset2.signal)
        np.testing.assert_array_equal(dataset1.anomaly_labels, dataset2.anomaly_labels)
    
    def test_different_random_seeds(self):
        """Test that different seeds produce different results."""
        signal_config = SignalConfig(
            length=100,
            noise_level=0.1,
            frequency=1.0
        )
        anomaly_config = AnomalyConfig(
            anomaly_probability=0.1,
            anomaly_magnitude=5.0,
            anomaly_duration=3
        )
        
        dataset1 = generate_synthetic_timeseries(
            signal_config, anomaly_config, random_seed=42
        )
        dataset2 = generate_synthetic_timeseries(
            signal_config, anomaly_config, random_seed=123
        )
        
        # Should be different
        assert not np.array_equal(dataset1.signal, dataset2.signal)
    
    def test_anomaly_ratio_validation(self):
        """Test that anomaly ratio is within expected bounds."""
        signal_config = SignalConfig(
            length=1000,
            noise_level=0.1,
            frequency=1.0
        )
        anomaly_config = AnomalyConfig(
            anomaly_probability=0.1,
            anomaly_magnitude=5.0,
            anomaly_duration=3
        )
        
        # Run multiple times to check expected ratio
        ratios = []
        for seed in range(10):
            dataset = generate_synthetic_timeseries(
                signal_config, anomaly_config, random_seed=seed
            )
            ratio = np.sum(dataset.anomaly_labels) / len(dataset.anomaly_labels)
            ratios.append(ratio)
        
        # Average ratio should be around 0.1 (with variance)
        avg_ratio = np.mean(ratios)
        assert 0.05 < avg_ratio < 0.20  # Within reasonable bounds
    
    def test_extreme_anomaly_magnitude(self):
        """Test with extreme anomaly magnitudes."""
        signal = np.sin(np.linspace(0, 10, 100))
        
        # Very large magnitude
        anomaly_config = AnomalyConfig(
            anomaly_probability=0.5,
            anomaly_magnitude=1e6,
            anomaly_duration=1
        )
        
        anomalous_signal, anomaly_labels = inject_point_anomalies(
            signal, anomaly_config, random_seed=42
        )
        assert len(anomalous_signal) == 100
        # Should not overflow
        assert not np.any(np.isinf(anomalous_signal))
        assert not np.any(np.isnan(anomalous_signal))
    
    def test_negative_anomaly_magnitude(self):
        """Test with negative anomaly magnitude."""
        signal = np.sin(np.linspace(0, 10, 100))
        
        anomaly_config = AnomalyConfig(
            anomaly_probability=0.5,
            anomaly_magnitude=-5.0,
            anomaly_duration=1
        )
        
        anomalous_signal, anomaly_labels = inject_point_anomalies(
            signal, anomaly_config, random_seed=42
        )
        assert len(anomalous_signal) == 100
        # Negative magnitude should still inject anomalies
        assert np.sum(anomaly_labels) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
