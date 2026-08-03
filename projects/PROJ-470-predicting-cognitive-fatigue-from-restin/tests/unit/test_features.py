import pytest
import numpy as np
import os
import sys
import tempfile
from pathlib import Path
import mne

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from features import calculate_lempel_ziv_complexity, process_eeg_segments, save_metrics_to_csv, load_config, setup_logger

class TestLempelZivComplexity:
    """Unit tests for LZC calculation."""

    def test_lzc_known_signal(self):
        """Test LZC calculation on a synthetic white noise signal."""
        # Generate synthetic white noise signal
        np.random.seed(42)
        duration = 120  # seconds
        sfreq = 256     # Hz
        n_samples = int(duration * sfreq)
        amplitude = 1.0
        
        signal = np.random.normal(0, amplitude, n_samples)
        
        # Calculate LZC
        lzc_value = calculate_lempel_ziv_complexity(signal)
        
        # Assert output is valid
        assert isinstance(lzc_value, float), "LZC value should be a float"
        assert not np.isnan(lzc_value), "LZC value should not be NaN"
        assert lzc_value > 0, "LZC value should be positive for white noise"
        
        # White noise should have relatively high complexity
        # The exact value depends on the implementation, but it should be non-trivial
        assert 0.1 < lzc_value < 10.0, f"LZC value {lzc_value} seems out of expected range for white noise"

    def test_lzc_constant_signal(self):
        """Test LZC on a constant signal (should be low complexity)."""
        signal = np.ones(1000)
        lzc_value = calculate_lempel_ziv_complexity(signal)
        
        assert isinstance(lzc_value, float)
        assert not np.isnan(lzc_value)
        assert lzc_value >= 0
        # Constant signal should have very low complexity
        assert lzc_value < 0.5, "Constant signal should have low LZC"

    def test_lzc_empty_signal(self):
        """Test LZC on an empty signal."""
        signal = np.array([])
        lzc_value = calculate_lempel_ziv_complexity(signal)
        
        assert lzc_value == 0.0

    def test_lzc_with_nans(self):
        """Test LZC calculation with NaN values in signal."""
        signal = np.random.normal(0, 1, 1000)
        signal[500] = np.nan
        
        # The function should handle NaNs gracefully (or we should filter them)
        # Our implementation filters them internally
        lzc_value = calculate_lempel_ziv_complexity(signal)
        
        assert isinstance(lzc_value, float)
        assert not np.isnan(lzc_value)

class TestProcessEegSegments:
    """Unit tests for EEG segment processing."""

    def test_process_single_channel(self):
        """Test processing a single channel EEG segment."""
        # Create a simple raw object
        np.random.seed(42)
        sfreq = 256
        duration = 2  # seconds (short for testing)
        n_samples = int(duration * sfreq)
        
        data = np.random.randn(1, n_samples)
        info = mne.create_info(ch_names=['EEG001'], sfreq=sfreq, ch_types='eeg')
        raw = mne.io.RawArray(data, info)
        
        config = load_config()
        logger = setup_logger('test')
        
        results = process_eeg_segments(raw, config, logger)
        
        assert len(results) == 1
        assert results[0]['participant_id'].startswith('participant_')
        assert results[0]['channel'] == 'EEG001'
        assert 'lzc_value' in results[0]
        assert isinstance(results[0]['lzc_value'], float)
        assert not np.isnan(results[0]['lzc_value'])

    def test_process_multiple_channels(self):
        """Test processing multiple channels."""
        np.random.seed(42)
        sfreq = 256
        duration = 2
        n_samples = int(duration * sfreq)
        
        # Create data for 2 channels
        data = np.random.randn(2, n_samples)
        ch_names = ['EEG001', 'EEG002']
        info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types='eeg')
        raw = mne.io.RawArray(data, info)
        
        config = load_config()
        logger = setup_logger('test')
        
        results = process_eeg_segments(raw, config, logger)
        
        assert len(results) == 2
        channels = [r['channel'] for r in results]
        assert 'EEG001' in channels
        assert 'EEG002' in channels

class TestSaveMetricsToCsv:
    """Unit tests for CSV saving."""

    def test_save_metrics(self):
        """Test saving metrics to CSV."""
        metrics = [
            {'participant_id': 'p1', 'channel': 'ch1', 'lzc_value': 0.5},
            {'participant_id': 'p1', 'channel': 'ch2', 'lzc_value': 0.6},
            {'participant_id': 'p2', 'channel': 'ch1', 'lzc_value': 0.55}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_metrics.csv'
            save_metrics_to_csv(metrics, str(output_path))
            
            assert output_path.exists()
            
            df = pd.read_csv(output_path)
            assert len(df) == 3
            assert list(df.columns) == ['participant_id', 'channel', 'lzc_value']
            assert df['participant_id'].iloc[0] == 'p1'
            assert df['lzc_value'].iloc[0] == 0.5

    def test_save_empty_metrics(self):
        """Test saving empty metrics list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'test_metrics.csv'
            
            with pytest.raises(ValueError, match="No metrics to save"):
                save_metrics_to_csv([], str(output_path))

# Import pandas here to avoid issues if not used in other tests
import pandas as pd

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
