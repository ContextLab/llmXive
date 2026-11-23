import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import mne

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from preprocessing import download_dataset, validate_dataset, EventSourceError, SampleSizeError
from config import get_config

class TestT010DownloadAndValidation:
    
    @patch('preprocessing.mne.datasets.openneuro.fetch')
    def test_download_dataset_success(self, mock_fetch, tmp_path):
        """Test successful dataset download."""
        mock_fetch.return_value = str(tmp_path / "ds0001171")
        
        # Create a fake BIDS structure for validation
        bids_dir = tmp_path / "ds0001171"
        bids_dir.mkdir(parents=True, exist_ok=True)
        (bids_dir / "dataset_description.json").write_text('{"Name": "Test", "BIDSVersion": "1.8.0"}')
        (bids_dir / "sub-01").mkdir()
        (bids_dir / "sub-01" / "eeg").mkdir()
        (bids_dir / "sub-01" / "eeg" / "sub-01_task-attention_eeg.edf").touch()
        (bids_dir / "sub-01" / "eeg" / "sub-01_task-attention_events.tsv").write_text("onset\tduration\ttrial_type\n1.0\t0\tactive")
        
        with patch('preprocessing.check_bids_structure', return_value=True), \
             patch('preprocessing.check_event_markers', return_value=True):
            
            result = download_dataset("ds0001171", str(tmp_path))
            assert Path(result).exists()
            mock_fetch.assert_called_once()

    @patch('preprocessing.mne.datasets.openneuro.fetch')
    def test_download_dataset_failure(self, mock_fetch, tmp_path):
        """Test that download failure raises RuntimeError."""
        mock_fetch.side_effect = Exception("Network error")
        
        with pytest.raises(RuntimeError, match="Dataset download failed"):
            download_dataset("ds0001171", str(tmp_path))

    def test_validate_dataset_bids_failure(self, tmp_path):
        """Test that non-BIDS structure raises ValueError."""
        fake_dir = tmp_path / "fake_dataset"
        fake_dir.mkdir()
        
        with patch('preprocessing.check_bids_structure', return_value=False), \
             patch('preprocessing.check_event_markers', return_value=True):
            
            with pytest.raises(ValueError, match="not a valid BIDS dataset"):
                validate_dataset(str(fake_dir))

    def test_validate_dataset_events_failure(self, tmp_path):
        """Test that missing event markers raise ValueError."""
        fake_dir = tmp_path / "fake_dataset"
        fake_dir.mkdir()
        (fake_dir / "dataset_description.json").write_text('{"Name": "Test", "BIDSVersion": "1.8.0"}')
        
        with patch('preprocessing.check_bids_structure', return_value=True), \
             patch('preprocessing.check_event_markers', return_value=False):
            
            with pytest.raises(ValueError, match="lacks required event markers"):
                validate_dataset(str(fake_dir))

    def test_validate_dataset_writes_metadata(self, tmp_path):
        """Test that validation writes metadata.json."""
        fake_dir = tmp_path / "fake_dataset"
        fake_dir.mkdir()
        (fake_dir / "dataset_description.json").write_text('{"Name": "Test", "BIDSVersion": "1.8.0"}')
        
        output_dir = tmp_path / "processed"
        output_dir.mkdir()
        
        # Mock config to point to our temp output dir
        with patch('preprocessing.get_config', return_value={'OUTPUT_PATH': str(output_dir)}), \
             patch('preprocessing.check_bids_structure', return_value=True), \
             patch('preprocessing.check_event_markers', return_value=True):
            
                validate_dataset(str(fake_dir))
                
                metadata_path = output_dir / "metadata.json"
                assert metadata_path.exists()
                
                with open(metadata_path) as f:
                    meta = json.load(f)
                
                assert "data_source_url" in meta
                assert "fetch_method" in meta
                assert meta["validation_status"] == "passed"