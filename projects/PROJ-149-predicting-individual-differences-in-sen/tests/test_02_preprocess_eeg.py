"""
tests/test_02_preprocess_eeg.py

Unit tests for EEG preprocessing pipeline.
"""

import os
import sys
import tempfile
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from config import get_path, ensure_dirs
from utils.eeg_helpers import bandpass_filter, notch_filter, reject_channels_by_variance, apply_ica

# Import functions to test
from importlib import import_module
preprocess_module = import_module('02_preprocess_eeg')

get_subject_id_from_path = preprocess_module.get_subject_id_from_path
load_physionet_eeg_data = preprocess_module.load_physionet_eeg_data
preprocess_subject = preprocess_module.preprocess_subject


class TestGetSubjectIdFromPath:
    """Tests for subject ID extraction from file paths."""
    
    def test_extract_sub_id_standard_format(self):
        """Test extraction from standard PhysioNet naming."""
        path = "/data/sub-001_task-rest_run-1_eeg.edf"
        assert get_subject_id_from_path(path) == "001"
    
    def test_extract_sub_id_simple_format(self):
        """Test extraction from simple naming."""
        path = "/data/sub-042_eeg.edf"
        assert get_subject_id_from_path(path) == "042"
    
    def test_extract_sub_id_uppercase(self):
        """Test extraction with uppercase extension."""
        path = "/data/sub-007_task-rest_eeg.EDF"
        assert get_subject_id_from_path(path) == "007"
    
    def test_extract_sub_id_invalid_path(self):
        """Test with invalid path."""
        path = "/data/random_file.txt"
        assert get_subject_id_from_path(path) is None
    
    def test_extract_sub_id_no_sub_prefix(self):
        """Test path without 'sub-' prefix."""
        path = "/data/001_eeg.edf"
        assert get_subject_id_from_path(path) is None


class TestLoadPhysionetEegData:
    """Tests for loading EEG data files."""
    
    @patch('pathlib.Path.rglob')
    def test_load_edf_files(self, mock_rglob):
        """Test loading .edf files."""
        mock_rglob.side_effect = [
            [Path('/data/sub-001_eeg.edf'), Path('/data/sub-002_eeg.edf')],
            []
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = load_physionet_eeg_data(tmpdir)
            
            assert len(result) == 2
            assert result[0]['subject_id'] == '001'
            assert result[1]['subject_id'] == '002'
    
    @patch('pathlib.Path.rglob')
    def test_load_no_files_error(self, mock_rglob):
        """Test error when no files found."""
        mock_rglob.return_value = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                load_physionet_eeg_data(tmpdir)

class TestPreprocessSubject:
    """Tests for subject preprocessing."""
    
    @patch('mne.io.read_raw_edf')
    @patch('mne.channels.make_standard_montage')
    @patch('02_preprocess_eeg.bandpass_filter')
    @patch('02_preprocess_eeg.notch_filter')
    @patch('02_preprocess_eeg.reject_channels_by_variance')
    @patch('02_preprocess_eeg.apply_ica')
    def test_preprocess_successful(
        self, mock_ica, mock_reject, mock_notch, mock_bandpass, 
        mock_montage, mock_read
    ):
        """Test successful preprocessing."""
        # Setup mocks
        mock_raw = MagicMock()
        mock_raw.ch_names = ['Cz', 'Fz', 'Pz', 'Oz', 'Fp1', 'Fp2']
        mock_raw.info = {'sfreq': 500.0}
        mock_read.return_value = mock_raw
        mock_montage.return_value = None
        mock_bandpass.return_value = mock_raw
        mock_notch.return_value = mock_raw
        mock_reject.return_value = (mock_raw, [])  # No channels rejected
        mock_ica.return_value = (mock_raw, 2)  # Remove 2 components
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = preprocess_subject(
                file_path='/data/sub-001_eeg.edf',
                subject_id='001',
                output_dir=tmpdir,
                no_ica=False
            )
            
            assert result['status'] == 'success'
            assert result['subject_id'] == '001'
            assert result['excluded'] is False
            assert result['channels_rejected'] == 0
            assert result['ica_components_removed'] == 2
            assert result['output_file'] is not None
    
    @patch('mne.io.read_raw_edf')
    @patch('mne.channels.make_standard_montage')
    @patch('02_preprocess_eeg.bandpass_filter')
    @patch('02_preprocess_eeg.notch_filter')
    @patch('02_preprocess_eeg.reject_channels_by_variance')
    def test_preprocess_excluded_high_rejection(
        self, mock_reject, mock_notch, mock_bandpass, 
        mock_montage, mock_read
    ):
        """Test exclusion when too many channels rejected."""
        # Setup mocks
        mock_raw = MagicMock()
        mock_raw.ch_names = ['Cz', 'Fz', 'Pz', 'Oz', 'Fp1', 'Fp2']
        mock_raw.info = {'sfreq': 500.0}
        mock_read.return_value = mock_raw
        mock_montage.return_value = None
        mock_bandpass.return_value = mock_raw
        mock_notch.return_value = mock_raw
        
        # Reject 3 out of 6 channels (50% > 30% threshold)
        mock_reject.return_value = (mock_raw, [0, 1, 2])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = preprocess_subject(
                file_path='/data/sub-001_eeg.edf',
                subject_id='001',
                output_dir=tmpdir,
                no_ica=True
            )
            
            assert result['status'] == 'excluded'
            assert result['excluded'] is True
            assert result['channels_rejected'] == 3
            assert result['rejection_rate'] == 0.5
    
    @patch('mne.io.read_raw_edf')
    def test_preprocess_error_handling(self, mock_read):
        """Test error handling when file read fails."""
        mock_read.side_effect = Exception("File not found")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = preprocess_subject(
                file_path='/data/nonexistent.edf',
                subject_id='999',
                output_dir=tmpdir,
                no_ica=True
            )
            
            assert result['status'] == 'error'
            assert 'Processing error' in result['message']
    
    @patch('mne.io.read_raw_edf')
    @patch('mne.channels.make_standard_montage')
    @patch('02_preprocess_eeg.bandpass_filter')
    @patch('02_preprocess_eeg.notch_filter')
    @patch('02_preprocess_eeg.reject_channels_by_variance')
    @patch('02_preprocess_eeg.apply_ica')
    def test_preprocess_no_ica_flag(
        self, mock_ica, mock_reject, mock_notch, mock_bandpass, 
        mock_montage, mock_read
    ):
        """Test that ICA is skipped when --no-ica flag is set."""
        mock_raw = MagicMock()
        mock_raw.ch_names = ['Cz', 'Fz', 'Pz']
        mock_raw.info = {'sfreq': 500.0}
        mock_read.return_value = mock_raw
        mock_montage.return_value = None
        mock_bandpass.return_value = mock_raw
        mock_notch.return_value = mock_raw
        mock_reject.return_value = (mock_raw, [])
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = preprocess_subject(
                file_path='/data/sub-001_eeg.edf',
                subject_id='001',
                output_dir=tmpdir,
                no_ica=True  # Skip ICA
            )
            
            # ICA should not be called
            mock_ica.assert_not_called()
            assert result['ica_components_removed'] == 0

class TestIntegration:
    """Integration tests for the preprocessing module."""
    
    def test_module_imports(self):
        """Test that all required functions are importable."""
        assert hasattr(preprocess_module, 'main')
        assert hasattr(preprocess_module, 'load_physionet_eeg_data')
        assert hasattr(preprocess_module, 'preprocess_subject')
        assert hasattr(preprocess_module, 'get_subject_id_from_path')
    
    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        assert callable(preprocess_module.main)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
