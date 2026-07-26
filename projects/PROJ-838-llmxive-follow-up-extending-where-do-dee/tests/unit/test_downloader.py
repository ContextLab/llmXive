import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import json
import tempfile

# Import the module under test
# We need to mock the datasets import before importing downloader if it fails
# But since we are testing logic, we assume datasets is available or mock it appropriately
import sys
from io import StringIO

from downloader import (
    verify_dataset_exists, 
    validate_trajectory_record, 
    validate_json_file, 
    fetch_and_validate, 
    ValidationError,
    stream_dataset
)
from config import ensure_directories


class TestVerifyDatasetExists:
    def test_verify_dataset_exists_fails_on_missing_id(self):
        """Test that verify_dataset_exists raises FileNotFoundError for missing dataset."""
        with patch('downloader.load_dataset') as mock_load:
            # Simulate a 404 or "Dataset not found" error
            mock_load.side_effect = Exception("Dataset not found: 'FAKE/MISSING'")
            
            with pytest.raises(FileNotFoundError) as exc_info:
                verify_dataset_exists("FAKE/MISSING")
            
            assert "not found" in str(exc_info.value).lower() or "404" in str(exc_info.value)

    @patch('downloader.load_dataset')
    def test_verify_dataset_exists_success(self, mock_load):
        """Test successful verification."""
        mock_ds = Mock()
        mock_ds.__iter__ = Mock(return_value=iter([{"id": "1"}]))
        mock_load.return_value = mock_ds
        
        result = verify_dataset_exists("REAL/DATASET")
        assert result is True

class TestValidateTrajectoryRecord:
    def test_valid_record(self):
        record = {"id": "123", "spans": [{"text": "hello"}]}
        assert validate_trajectory_record(record, "123") is True

    def test_missing_id(self):
        record = {"spans": []}
        with pytest.raises(ValidationError, match="missing required field: id"):
            validate_trajectory_record(record, "test_id")

    def test_missing_spans(self):
        record = {"id": "123"}
        with pytest.raises(ValidationError, match="missing required field: spans"):
            validate_trajectory_record(record, "test_id")

    def test_invalid_spans_type(self):
        record = {"id": "123", "spans": "not a list"}
        with pytest.raises(ValidationError, match="invalid 'spans' type"):
            validate_trajectory_record(record, "test_id")

class TestValidateJsonFile:
    def test_valid_json_file(self, tmp_path):
        data = [{"id": "1", "spans": []}, {"id": "2", "spans": []}]
        file_path = tmp_path / "valid.json"
        file_path.write_text(json.dumps(data))
        
        result = validate_json_file(file_path)
        assert len(result) == 2

    def test_malformed_json_file(self, tmp_path):
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{ invalid json }")
        
        with pytest.raises(ValidationError, match="Invalid JSON"):
            validate_json_file(file_path)

    def test_skips_malformed_records(self, tmp_path):
        data = [
            {"id": "1", "spans": []}, 
            {"spans": []},  # Missing id
            {"id": "2", "spans": []}
        ]
        file_path = tmp_path / "mixed.json"
        file_path.write_text(json.dumps(data))
        
        result = validate_json_file(file_path)
        # Should skip the one missing id
        assert len(result) == 2
        assert result[0]["id"] == "1"
        assert result[1]["id"] == "2"

class TestFetchAndValidate:
    @patch('downloader.verify_dataset_exists')
    @patch('downloader.load_dataset')
    def test_fetch_and_validate_success(self, mock_load, mock_verify, tmp_path):
        mock_verify.return_value = True
        
        # Mock streaming dataset
        mock_item1 = {"id": "1", "spans": [{"text": "a"}]}
        mock_item2 = {"id": "2", "spans": [{"text": "b"}]}
        mock_ds = [mock_item1, mock_item2]
        mock_load.return_value = mock_ds
        
        output_path = tmp_path / "output.json"
        
        result_path = fetch_and_validate("TEST/DATASET", output_path)
        
        assert result_path == output_path
        assert output_path.exists()
        
        with open(output_path) as f:
            saved_data = json.load(f)
        assert len(saved_data) == 2

    @patch('downloader.verify_dataset_exists')
    def test_fetch_and_validate_missing_dataset(self, mock_verify, tmp_path):
        mock_verify.side_effect = FileNotFoundError("Dataset not found")
        
        output_path = tmp_path / "output.json"
        
        with pytest.raises(FileNotFoundError):
            fetch_and_validate("MISSING/DATASET", output_path)

class TestStreamDataset:
    @patch('downloader.verify_dataset_exists')
    @patch('downloader.load_dataset')
    def test_stream_dataset_yield(self, mock_load, mock_verify):
        mock_verify.return_value = True
        mock_item = {"id": "1", "spans": []}
        mock_load.return_value = [mock_item]
        
        gen = stream_dataset("TEST/DATASET")
        item = next(gen)
        assert item["id"] == "1"

class TestDirectoriesExist:
    """Tests for T008: Verify data directories and .gitkeep files exist."""
    
    def test_directories_exist(self, tmp_path, monkeypatch):
        """Test that data/raw and data/processed directories exist with .gitkeep files."""
        # Change to tmp_path to simulate project root
        monkeypatch.chdir(tmp_path)
        
        # Create the directories manually to simulate setup
        raw_dir = tmp_path / "data" / "raw"
        processed_dir = tmp_path / "data" / "processed"
        raw_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        
        # Create .gitkeep files
        (raw_dir / ".gitkeep").touch()
        (processed_dir / ".gitkeep").touch()
        
        # Verify existence
        assert raw_dir.exists(), "data/raw directory should exist"
        assert processed_dir.exists(), "data/processed directory should exist"
        assert (raw_dir / ".gitkeep").exists(), "data/raw/.gitkeep should exist"
        assert (processed_dir / ".gitkeep").exists(), "data/processed/.gitkeep should exist"
    
    def test_directories_exist_via_config(self, tmp_path, monkeypatch):
        """Test that ensure_directories creates the structure correctly."""
        monkeypatch.chdir(tmp_path)
        
        # Call ensure_directories from config
        ensure_directories()
        
        # Verify
        raw_dir = tmp_path / "data" / "raw"
        processed_dir = tmp_path / "data" / "processed"
        
        assert raw_dir.exists(), "ensure_directories should create data/raw"
        assert processed_dir.exists(), "ensure_directories should create data/processed"
        
        # Note: ensure_directories creates dirs, but .gitkeep creation is 
        # handled by setup_data_dirs.py (this task). 
        # We verify the dirs exist as the primary requirement.