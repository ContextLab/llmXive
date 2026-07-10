import pytest
import json
import tempfile
import os
from pathlib import Path
import numpy as np
import mne

from code.analysis.metrics import generate_metrics_summary
from code.config import get_config

class TestGenerateMetricsSummary:
    """
    Unit tests for T031: generate_metrics_summary function.
    """

    def test_generate_metrics_summary_structure(self, mocker):
        """
        Test that the function returns a dictionary with the correct structure
        and saves a valid JSON file.
        """
        # Mock the analysis functions to return dummy data
        # This allows us to test the aggregation logic without needing real T027-T030 implementations
        mock_latency = 150.5
        mock_amplitude = 2.3
        mock_window = "100-200ms"

        mocker.patch('code.analysis.metrics.compute_difference_wave_auditory', return_value=np.random.rand(100))
        mocker.patch('code.analysis.metrics.compute_difference_wave_visual', return_value=np.random.rand(100))
        mocker.patch('code.analysis.metrics.extract_peak_latency', return_value=(mock_latency, mock_window))
        mocker.patch('code.analysis.metrics.extract_mean_amplitude', return_value=(mock_amplitude, mock_window))

        # Create a temporary dummy FIF file
        with tempfile.NamedTemporaryFile(suffix='.fif', delete=False) as tmp_in:
            # Create a minimal raw object
            info = mne.create_info(ch_names=['EEG 001', 'EEG 002'], sfreq=500, ch_types='eeg')
            data = np.random.rand(2, 1000)
            raw = mne.io.RawArray(data, info)
            raw.save(tmp_in.name, overwrite=True)
            tmp_in_path = Path(tmp_in.name)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_out = Path(tmp_dir) / 'metrics_summary.json'

            # Run the function
            result = generate_metrics_summary(data_path=tmp_in_path, output_path=tmp_out)

            # Verify return structure
            assert 'auditory' in result
            assert 'visual' in result
            assert 'metadata' in result
            
            assert result['auditory']['status'] == 'success'
            assert result['visual']['status'] == 'success'
            
            assert result['auditory']['peak_latency_ms'] == mock_latency
            assert result['auditory']['mean_amplitude_uv'] == mock_amplitude
            assert result['visual']['peak_latency_ms'] == mock_latency
            assert result['visual']['mean_amplitude_uv'] == mock_amplitude

            # Verify JSON file was created and is valid
            assert tmp_out.exists()
            with open(tmp_out, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == result

        # Cleanup
        os.unlink(tmp_in_path)

    def test_generate_metrics_summary_missing_data(self):
        """
        Test that the function raises FileNotFoundError if input data is missing.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            non_existent = Path(tmp_dir) / 'non_existent.fif'
            non_existent_out = Path(tmp_dir) / 'out.json'

            with pytest.raises(FileNotFoundError):
                generate_metrics_summary(data_path=non_existent, output_path=non_existent_out)

    def test_generate_metrics_summary_partial_failure(self, mocker):
        """
        Test that the function handles failure in one modality gracefully
        and still returns results for the other.
        """
        # Mock auditory success
        mocker.patch('code.analysis.metrics.compute_difference_wave_auditory', return_value=np.random.rand(100))
        mocker.patch('code.analysis.metrics.extract_peak_latency', side_effect=[(150.0, '100-200ms'), Exception("Simulated error")])
        mocker.patch('code.analysis.metrics.extract_mean_amplitude', return_value=(2.0, '100-200ms'))
        
        # Mock visual failure in difference wave
        mocker.patch('code.analysis.metrics.compute_difference_wave_visual', side_effect=Exception("Visual error"))

        with tempfile.NamedTemporaryFile(suffix='.fif', delete=False) as tmp_in:
            info = mne.create_info(ch_names=['EEG 001'], sfreq=500, ch_types='eeg')
            data = np.random.rand(1, 1000)
            raw = mne.io.RawArray(data, info)
            raw.save(tmp_in.name, overwrite=True)
            tmp_in_path = Path(tmp_in.name)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_out = Path(tmp_dir) / 'metrics_summary.json'

            result = generate_metrics_summary(data_path=tmp_in_path, output_path=tmp_out)

            assert result['auditory']['status'] == 'success'
            assert result['visual']['status'] == 'failed'
            assert 'error' in result['visual']

        os.unlink(tmp_in_path)
