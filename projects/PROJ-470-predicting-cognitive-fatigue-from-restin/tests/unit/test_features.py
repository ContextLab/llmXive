import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from features import calculate_permutation_entropy, calculate_lzc, process_eeg_segments, save_metrics_to_csv
from models.complexity_metric import MetricType, ComplexityMetric

class TestPermutationEntropy:
    """Unit tests for permutation entropy calculation."""

    def test_permutation_entropy_known_signal(self):
        """Test PE on a known signal with expected properties."""
        # Create a signal with high regularity (low entropy)
        # A perfectly periodic signal should have low permutation entropy
        signal = np.sin(np.linspace(0, 10 * np.pi, 1000))
        sampling_rate = 256
        
        pe = calculate_permutation_entropy(signal, sampling_rate, order=3, delay=1)
        
        # PE should be between 0 and 1
        assert 0 <= pe <= 1, f"PE value {pe} is outside [0, 1] range"
        
        # For a sine wave, PE should be relatively low (not random)
        # The exact value depends on the embedding dimension, but it should be < 0.8
        assert pe < 0.8, f"Sine wave PE {pe} seems too high for a regular signal"

    def test_permutation_entropy_random_signal(self):
        """Test PE on a random signal (high entropy)."""
        # Create a random signal
        np.random.seed(42)
        signal = np.random.randn(1000)
        sampling_rate = 256
        
        pe = calculate_permutation_entropy(signal, sampling_rate, order=3, delay=1)
        
        # PE should be between 0 and 1
        assert 0 <= pe <= 1, f"PE value {pe} is outside [0, 1] range"
        
        # For a random signal, PE should be relatively high (close to 1)
        assert pe > 0.5, f"Random signal PE {pe} seems too low"

    def test_permutation_entropy_short_signal(self):
        """Test PE on a signal that is too short."""
        signal = np.array([1.0, 2.0, 3.0])
        sampling_rate = 256
        
        pe = calculate_permutation_entropy(signal, sampling_rate, order=5, delay=1)
        
        # Should return 0 for too short signal
        assert pe == 0.0, f"Short signal PE should be 0, got {pe}"

    def test_permutation_entropy_constant_signal(self):
        """Test PE on a constant signal (should have low entropy)."""
        signal = np.ones(1000)
        sampling_rate = 256
        
        pe = calculate_permutation_entropy(signal, sampling_rate, order=3, delay=1)
        
        # PE should be 0 for a constant signal
        assert pe == 0.0, f"Constant signal PE should be 0, got {pe}"

class TestLempelZivComplexity:
    """Unit tests for Lempel-Ziv complexity calculation."""

    def test_lzc_known_signal(self):
        """Test LZC on a known signal."""
        # Create a periodic signal
        signal = np.sin(np.linspace(0, 10 * np.pi, 1000))
        sampling_rate = 256
        
        lzc = calculate_lzc(signal, sampling_rate)
        
        # LZC should be between 0 and 1 (normalized)
        assert 0 <= lzc <= 1, f"LZC value {lzc} is outside [0, 1] range"

    def test_lzc_random_signal(self):
        """Test LZC on a random signal (should be higher)."""
        np.random.seed(42)
        signal = np.random.randn(1000)
        sampling_rate = 256
        
        lzc = calculate_lzc(signal, sampling_rate)
        
        # LZC should be between 0 and 1
        assert 0 <= lzc <= 1, f"LZC value {lzc} is outside [0, 1] range"
        
        # Random signal should have higher LZC than periodic signal
        periodic_signal = np.sin(np.linspace(0, 10 * np.pi, 1000))
        lzc_periodic = calculate_lzc(periodic_signal, sampling_rate)
        
        assert lzc > lzc_periodic, "Random signal should have higher LZC than periodic signal"

class TestProcessEegSegments:
    """Unit tests for EEG segment processing."""

    def test_process_eeg_segments(self):
        """Test processing of EEG segments."""
        # Create mock EEG data
        eeg_data = [
            {
                'data': np.sin(np.linspace(0, np.pi, 500)),
                'metadata': {
                    'segment_id': 'seg1',
                    'participant_id': 'p1',
                    'channel': 'Fz',
                    'sampling_rate': 256,
                    'condition': 'resting'
                }
            },
            {
                'data': np.random.randn(500),
                'metadata': {
                    'segment_id': 'seg2',
                    'participant_id': 'p1',
                    'channel': 'Cz',
                    'sampling_rate': 256,
                    'condition': 'resting'
                }
            }
        ]
        
        config = {
            'lzc': {},
            'permutation_entropy': {'order': 3, 'delay': 1}
        }
        
        metrics = process_eeg_segments(eeg_data, config)
        
        # Should have 4 metrics (2 segments * 2 metrics each)
        assert len(metrics) == 4, f"Expected 4 metrics, got {len(metrics)}"
        
        # Check metric types
        metric_types = [m.metric_type for m in metrics]
        assert MetricType.LZC in metric_types, "LZC metric should be present"
        assert MetricType.PE in metric_types, "PE metric should be present"

class TestSaveMetricsToCsv:
    """Unit tests for saving metrics to CSV."""

    def test_save_metrics_to_csv(self, tmp_path):
        """Test saving metrics to a CSV file."""
        # Create mock metrics
        metrics = [
            ComplexityMetric(
                metric_type=MetricType.PE,
                value=0.5,
                participant_id='p1',
                segment_id='seg1',
                channel='Fz',
                condition='resting',
                metadata={}
            ),
            ComplexityMetric(
                metric_type=MetricType.LZC,
                value=0.3,
                participant_id='p1',
                segment_id='seg1',
                channel='Fz',
                condition='resting',
                metadata={}
            )
        ]
        
        output_path = tmp_path / "test_metrics.csv"
        save_metrics_to_csv(metrics, output_path)
        
        # Check if file exists
        assert output_path.exists(), "Output CSV file should exist"
        
        # Check content
        df = pd.read_csv(output_path)
        assert len(df) == 2, f"Expected 2 rows, got {len(df)}"
        assert 'metric_type' in df.columns, "metric_type column should exist"
        assert 'value' in df.columns, "value column should exist"
        assert 'participant_id' in df.columns, "participant_id column should exist"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])