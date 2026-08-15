import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

import mne
import numpy as np

from code.data.download import (
    fetch_visual_dataset,
    validate_visual_dataset,
    run_visual_validation,
    DownloadValidationError,
    _extract_visual_metadata,
    _validate_visual_structure
)
from code.config import get_config

class TestVisualDownload:
    """Tests for visual dataset download functionality (T016)."""
    
    @pytest.fixture
    def temp_dataset_dir(self):
        """Create a temporary directory for dataset storage."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @patch('mne.datasets.fetch_openneuro_dataset')
    def test_fetch_visual_dataset_success(self, mock_fetch, temp_dataset_dir):
        """Test successful fetch of visual dataset."""
        # Setup mock
        mock_path = Path(temp_dataset_dir) / "ds000117"
        mock_path.mkdir(parents=True, exist_ok=True)
        
        # Create minimal BIDS structure
        (mock_path / "dataset_description.json").write_text('{"Name": "Test", "BIDSVersion": "1.6.0"}')
        
        mock_fetch.return_value = str(mock_path)
        
        # Mock the metadata extraction
        with patch('code.data.download._extract_visual_metadata') as mock_meta:
            mock_meta.return_value = {
                "dataset_id": "ds000117",
                "modality": "visual",
                "path": str(mock_path),
                "sampling_rate": 1000.0
            }
            
            # Run fetch
            dataset_path, metadata = fetch_visual_dataset(output_dir=temp_dataset_dir)
            
            # Assertions
            assert dataset_path.exists()
            assert metadata["dataset_id"] == "ds000117"
            assert metadata["modality"] == "visual"
            mock_fetch.assert_called_once()
    
    @patch('mne.datasets.fetch_openneuro_dataset')
    def test_fetch_visual_dataset_failure(self, mock_fetch, temp_dataset_dir):
        """Test fetch failure when dataset cannot be downloaded."""
        mock_fetch.side_effect = Exception("Network error")
        
        with pytest.raises(DownloadValidationError):
            fetch_visual_dataset(output_dir=temp_dataset_dir)
    
    def test_extract_visual_metadata(self, temp_dataset_dir):
        """Test metadata extraction from visual dataset."""
        dataset_path = Path(temp_dataset_dir) / "ds000117"
        dataset_path.mkdir(parents=True, exist_ok=True)
        
        # Create minimal BIDS structure
        desc_file = dataset_path / "dataset_description.json"
        desc_file.write_text('{"Name": "Visual Oddball", "BIDSVersion": "1.6.0"}')
        
        metadata = _extract_visual_metadata(dataset_path)
        
        assert metadata["dataset_id"] == "ds000117"
        assert metadata["modality"] == "visual"
        assert "description" in metadata
    
    def test_validate_visual_structure_valid(self, temp_dataset_dir):
        """Test validation of a valid visual dataset structure."""
        dataset_path = Path(temp_dataset_dir) / "ds000117"
        dataset_path.mkdir(parents=True, exist_ok=True)
        
        # Create minimal BIDS structure
        (dataset_path / "dataset_description.json").write_text('{"Name": "Test", "BIDSVersion": "1.6.0"}')
        
        metadata = {
            "dataset_id": "ds000117",
            "modality": "visual",
            "sampling_rate": 1000.0
        }
        
        # Should not raise
        _validate_visual_structure(dataset_path, metadata)
    
    def test_validate_visual_structure_invalid_sampling_rate(self, temp_dataset_dir):
        """Test validation fails for low sampling rate."""
        dataset_path = Path(temp_dataset_dir) / "ds000117"
        dataset_path.mkdir(parents=True, exist_ok=True)
        
        (dataset_path / "dataset_description.json").write_text('{"Name": "Test", "BIDSVersion": "1.6.0"}')
        
        metadata = {
            "dataset_id": "ds000117",
            "modality": "visual",
            "sampling_rate": 250.0  # Below 500 Hz requirement
        }
        
        with pytest.raises(DownloadValidationError):
            _validate_visual_structure(dataset_path, metadata)
    
    @patch('code.data.download.fetch_visual_dataset')
    def test_validate_visual_dataset_success(self, mock_fetch, temp_dataset_dir):
        """Test successful validation of visual dataset."""
        mock_path = Path(temp_dataset_dir) / "ds000117"
        mock_path.mkdir(parents=True, exist_ok=True)
        (mock_path / "dataset_description.json").write_text('{"Name": "Test", "BIDSVersion": "1.6.0"}')
        
        mock_fetch.return_value = (mock_path, {
            "dataset_id": "ds000117",
            "modality": "visual",
            "sampling_rate": 1000.0
        })
        
        result = validate_visual_dataset(mock_path)
        
        assert result["valid"] is True
        assert result["dataset_id"] == "ds000117"
    
    @patch('code.data.download.fetch_visual_dataset')
    def test_validate_visual_dataset_low_sampling_rate(self, mock_fetch, temp_dataset_dir):
        """Test validation fails for low sampling rate."""
        mock_path = Path(temp_dataset_dir) / "ds000117"
        mock_path.mkdir(parents=True, exist_ok=True)
        
        mock_fetch.return_value = (mock_path, {
            "dataset_id": "ds000117",
            "modality": "visual",
            "sampling_rate": 250.0
        })
        
        with pytest.raises(DownloadValidationError):
            validate_visual_dataset(mock_path)
    
    @patch('code.data.download.fetch_visual_dataset')
    def test_run_visual_validation(self, mock_fetch, temp_dataset_dir):
        """Test full validation pipeline."""
        mock_path = Path(temp_dataset_dir) / "ds000117"
        mock_path.mkdir(parents=True, exist_ok=True)
        (mock_path / "dataset_description.json").write_text('{"Name": "Test", "BIDSVersion": "1.6.0"}')
        
        mock_fetch.return_value = (mock_path, {
            "dataset_id": "ds000117",
            "modality": "visual",
            "sampling_rate": 1000.0
        })
        
        result = run_visual_validation()
        
        assert result["valid"] is True
        assert result["modality"] == "visual"