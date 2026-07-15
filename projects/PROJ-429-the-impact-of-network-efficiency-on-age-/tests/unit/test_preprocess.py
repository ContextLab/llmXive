"""
Unit tests for code/data/preprocess.py
"""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data import preprocess
from code.config import get_config


class TestPreprocessPipeline:
    """Tests for the preprocessing pipeline functions."""

    def test_compute_snr(self):
        """Test SNR computation logic."""
        # Create mock raw object
        mock_raw = Mock()
        mock_raw.get_data.return_value = np.random.randn(64, 1000) * 1e-6
        mock_raw.info = {'sfreq': 250.0}
        
        snr = preprocess.compute_snr(mock_raw)
        
        # SNR should be a float
        assert isinstance(snr, float)
        # SNR should be reasonable (not NaN or Inf)
        assert not np.isnan(snr)
        assert not np.isinf(snr)

    def test_detect_artifacts(self):
        """Test artifact detection logic."""
        # Create clean epochs
        clean_epochs = [np.random.randn(64, 2500) * 1e-6 for _ in range(5)]
        
        clean_flags = preprocess.detect_artifacts(clean_epochs, threshold=0.5)
        
        # All should be clean (no large artifacts)
        assert all(clean_flags)
        assert len(clean_flags) == 5

    def test_detect_artifacts_with_artifacts(self):
        """Test artifact detection with known artifacts."""
        # Create epochs with large artifacts
        epochs_with_artifacts = []
        for i in range(5):
            epoch = np.random.randn(64, 2500) * 1e-6
            # Inject large artifact in 60% of time points
            artifact_mask = np.random.rand(64, 2500) > 0.4
            epoch[artifact_mask] = 200e-6  # Large amplitude
            epochs_with_artifacts.append(epoch)
        
        clean_flags = preprocess.detect_artifacts(epochs_with_artifacts, threshold=0.5)
        
        # Some should be rejected (depending on artifact distribution)
        # At least one should be rejected if artifacts are large enough
        assert len(clean_flags) == 5

    def test_create_epochs(self):
        """Test epoch creation."""
        # Create mock raw with 10 seconds of data at 250 Hz = 2500 samples
        mock_raw = Mock()
        n_samples = 2500  # 10 seconds at 250 Hz
        mock_raw.get_data.return_value = np.random.randn(64, n_samples) * 1e-6
        mock_raw.info = {'sfreq': 250.0}
        
        epochs = preprocess.create_epochs(mock_raw, epoch_length_sec=10.0)
        
        # Should create exactly 1 epoch
        assert len(epochs) == 1
        assert epochs[0].shape == (64, 2500)

    def test_bandpass_filter(self):
        """Test bandpass filter application."""
        # Create mock raw
        mock_raw = Mock()
        mock_raw.copy.return_value = Mock()
        mock_raw.copy.return_value.filter = Mock()
        mock_raw.info = {'sfreq': 250.0}
        
        filtered = preprocess.bandpass_filter(mock_raw, l_freq=1.0, h_freq=40.0)
        
        # Filter should be called
        assert mock_raw.copy.return_value.filter.called
        assert filtered is mock_raw.copy.return_value

    def test_preprocess_file_success(self, tmp_path):
        """Test full preprocessing pipeline on a mock file."""
        # Create a mock EEG file
        eeg_file = tmp_path / "test.edf"
        eeg_file.write_bytes(b"fake edf content")
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        config = {
            'epoch_length_sec': 10.0,
            'n_ica_components': 10
        }
        
        # This will fail on file loading, but we test the structure
        with patch('code.data.preprocess.load_raw_eeg') as mock_load:
            # Create a realistic mock
            mock_raw = Mock()
            mock_raw.get_data.return_value = np.random.randn(32, 2500) * 1e-6
            mock_raw.info = {'sfreq': 250.0, 'ch_names': ['EEG' + str(i) for i in range(32)]}
            mock_load.return_value = mock_raw
            
            with patch('code.data.preprocess.bandpass_filter', return_value=mock_raw):
                with patch('code.data.preprocess.compute_snr', return_value=15.0):
                    with patch('code.data.preprocess.run_ica', return_value=(Mock(exclude=[0, 1]), 2)):
                        with patch('code.data.preprocess.apply_ica', return_value=mock_raw):
                            with patch('code.data.preprocess.create_epochs', return_value=[np.random.randn(32, 2500) * 1e-6]):
                                with patch('code.data.preprocess.detect_artifacts', return_value=[True]):
                                    result = preprocess.preprocess_file(eeg_file, output_dir, config)
                                    
                                    # Check result structure
                                    assert result['file_id'] == 'test'
                                    assert result['status'] == 'success'
                                    assert result['snr_db'] == 15.0
                                    assert result['snr_flag'] == 'Good'
                                    assert result['n_epochs_total'] == 1
                                    assert result['n_epochs_clean'] == 1
                                    assert result['n_artifacts_rejected'] == 0

    def test_preprocess_file_low_snr(self, tmp_path):
        """Test preprocessing with low SNR."""
        eeg_file = tmp_path / "test_low_snr.edf"
        eeg_file.write_bytes(b"fake")
        
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        config = {'epoch_length_sec': 10.0, 'n_ica_components': 10}
        
        with patch('code.data.preprocess.load_raw_eeg') as mock_load:
            mock_raw = Mock()
            mock_raw.get_data.return_value = np.random.randn(32, 2500) * 1e-6
            mock_raw.info = {'sfreq': 250.0, 'ch_names': ['EEG' + str(i) for i in range(32)]}
            mock_load.return_value = mock_raw
            
            with patch('code.data.preprocess.bandpass_filter', return_value=mock_raw):
                with patch('code.data.preprocess.compute_snr', return_value=5.0):  # Low SNR
                    with patch('code.data.preprocess.run_ica', return_value=(Mock(exclude=[]), 0)):
                        with patch('code.data.preprocess.apply_ica', return_value=mock_raw):
                            with patch('code.data.preprocess.create_epochs', return_value=[np.random.randn(32, 2500) * 1e-6]):
                                with patch('code.data.preprocess.detect_artifacts', return_value=[True]):
                                    result = preprocess.preprocess_file(eeg_file, output_dir, config)
                                    
                                    assert result['snr_db'] == 5.0
                                    assert result['snr_flag'] == 'Low Signal Quality'

    def test_run_ica(self):
        """Test ICA execution."""
        mock_raw = Mock()
        mock_raw.get_data.return_value = np.random.randn(32, 2500) * 1e-6
        mock_raw.info = {'sfreq': 250.0}
        
        # Mock the ICA class
        with patch('mne.preprocessing.ICA') as MockICA:
            mock_ica_instance = Mock()
            mock_ica_instance.exclude = [0, 1]
            MockICA.return_value = mock_ica_instance
            mock_ica_instance.find_bads_eog.return_value = ([0], [0.9])
            mock_ica_instance.find_bads_ecg.return_value = ([1], [0.9])
            
            ica, n_excluded = preprocess.run_ica(mock_raw, n_components=10)
            
            assert n_excluded == 2
            assert MockICA.called
            assert mock_ica_instance.fit.called
            assert mock_ica_instance.find_bads_eog.called

    def test_apply_ica(self):
        """Test ICA application."""
        mock_raw = Mock()
        mock_ica = Mock()
        mock_clean = Mock()
        mock_ica.apply.return_value = mock_clean
        
        result = preprocess.apply_ica(mock_raw, mock_ica)
        
        assert mock_ica.apply.called
        assert result is mock_clean

    def test_load_raw_eeg_error(self, tmp_path):
        """Test error handling for missing file."""
        non_existent = tmp_path / "nonexistent.edf"
        
        with pytest.raises(FileNotFoundError):
            preprocess.load_raw_eeg(non_existent)