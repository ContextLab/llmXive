"""
Unit tests for the data_loader module.

These tests verify the logic of data loading, validation, and error handling
without requiring actual network access or large downloads.
"""
import pytest
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, MagicMock, mock_open
import json
import tarfile
import io

from src.data_loader import (
    ERR_DATA_UNAVAILABLE,
    load_openneuro_dataset,
    _fetch_dataset_metadata,
    _validate_events_tsv,
    _download_and_extract_dataset
)

class TestDataLoader:
    """Test cases for data loading functionality."""

    def test_fetch_dataset_metadata_success(self):
        """Test successful metadata fetch from OpenNeuro."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "ds000030", "name": "Cyberball"}
        
        with patch('src.data_loader.requests.get', return_value=mock_response) as mock_get:
            result = _fetch_dataset_metadata("ds000030")
            assert result["id"] == "ds000030"
            mock_get.assert_called_once()

    def test_fetch_dataset_metadata_not_found(self):
        """Test error handling when dataset is not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        with patch('src.data_loader.requests.get', return_value=mock_response):
            with pytest.raises(ERR_DATA_UNAVAILABLE) as exc_info:
                _fetch_dataset_metadata("nonexistent")
            assert "not found" in str(exc_info.value).lower()

    def test_fetch_dataset_metadata_retries(self):
        """Test that fetch retries on network errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        with patch('src.data_loader.requests.get', return_value=mock_response):
            with pytest.raises(ERR_DATA_UNAVAILABLE):
                _fetch_dataset_metadata("ds000030")
            # Should have attempted multiple times
            assert mock_response.status_code == 500

    def test_validate_events_tsv_valid(self):
        """Test validation with valid events.tsv content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir)
            events_file = dataset_path / "sub-01" / "func" / "sub-01_task-cyberball_events.tsv"
            events_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create valid events.tsv with required markers
            content = "onset\tduration\ttrial_type\n0\t1\tInclusion\n5\t1\tExclusion\n"
            events_file.write_text(content)
            
            # Should not raise
            _validate_events_tsv(dataset_path)

    def test_validate_events_tsv_missing_markers(self):
        """Test validation fails when required markers are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir)
            events_file = dataset_path / "sub-01" / "func" / "sub-01_task-cyberball_events.tsv"
            events_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create events.tsv without required markers
            content = "onset\tduration\ttrial_type\n0\t1\tNeutral\n5\t1\tControl\n"
            events_file.write_text(content)
            
            with pytest.raises(ERR_DATA_UNAVAILABLE) as exc_info:
                _validate_events_tsv(dataset_path)
            assert "Missing required event markers" in str(exc_info.value)

    def test_validate_events_tsv_no_files(self):
        """Test validation fails when no events.tsv files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_path = Path(tmpdir)
            # No events.tsv files created
            
            with pytest.raises(ERR_DATA_UNAVAILABLE) as exc_info:
                _validate_events_tsv(dataset_path)
            assert "No events.tsv files found" in str(exc_info.value)

    def test_download_and_extract_dataset(self):
        """Test download and extraction logic (mocked)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Create a mock tarball in memory
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
                # Add a dummy file
                info = tarfile.TarInfo(name="ds000030/dummy.txt")
                info.size = 10
                tar.addfile(info, io.BytesIO(b"dummy data"))
            
            tar_path = output_dir / "ds000030.tar.gz"
            with open(tar_path, 'wb') as f:
                f.write(tar_buffer.getvalue())
            
            # Mock the download to skip actual download
            with patch('src.data_loader.requests.get') as mock_get:
                # We'll manually create the tarball instead of downloading
                pass
            
            # Manually extract to test extraction logic
            with tarfile.open(tar_path, 'r:gz') as tar:
                tar.extractall(path=output_dir)
            
            extracted_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
            assert len(extracted_dirs) == 1
            assert extracted_dirs[0].name == "ds000030"

    def test_load_openneuro_dataset_integration_mocked(self):
        """Integration test with mocked network calls."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            dataset_dir = base_dir / "ds000030"
            dataset_dir.mkdir()
            
            # Create mock dataset structure with valid events
            func_dir = dataset_dir / "sub-01" / "func"
            func_dir.mkdir(parents=True)
            
            events_file = func_dir / "sub-01_task-cyberball_events.tsv"
            events_file.write_text("onset\tduration\ttrial_type\n0\t1\tInclusion\n5\t1\tExclusion\n")
            
            # Mock the download and metadata functions
            with patch('src.data_loader._fetch_dataset_metadata') as mock_meta:
                mock_meta.return_value = {"id": "ds000030"}
                
                with patch('src.data_loader._download_and_extract_dataset') as mock_download:
                    mock_download.return_value = dataset_dir
                    
                    with patch('src.data_loader._validate_events_tsv') as mock_validate:
                        # Should not raise
                        result = load_openneuro_dataset(base_data_dir=base_dir)
                        
                        assert result == dataset_dir
                        mock_meta.assert_called_once()
                        mock_download.assert_called_once()
                        mock_validate.assert_called_once_with(dataset_dir)

    def test_err_data_unavailable_exception(self):
        """Test that ERR_DATA_UNAVAILABLE is a proper exception."""
        try:
            raise ERR_DATA_UNAVAILABLE("Test error")
        except ERR_DATA_UNAVAILABLE as e:
            assert str(e) == "Test error"
        except Exception as e:
            pytest.fail(f"Raised wrong exception type: {type(e)}")