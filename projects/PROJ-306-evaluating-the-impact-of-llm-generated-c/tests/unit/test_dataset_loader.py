"""
Unit tests for dataset_loader.py (T006a).
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Mock the datasets module to avoid network calls in unit tests
import sys
from unittest.mock import MagicMock, patch

# Create a mock for datasets before importing dataset_loader
mock_datasets = MagicMock()
mock_dataset_obj = MagicMock()
mock_dataset_obj.to_list.return_value = [
    {"task_id": 1, "prompt": "def add(a, b):", "code": "return a + b", "test_list": ["assert add(1,2)==3"]},
    {"task_id": 2, "prompt": "def mul(a, b):", "code": "return a * b", "test_list": ["assert mul(2,2)==4"]}
]
mock_datasets.load_dataset.return_value = mock_dataset_obj
sys.modules['datasets'] = mock_datasets

from dataset_loader import load_mbpp_dataset, save_raw_mbpp_files


class TestDatasetLoader:
    @patch('dataset_loader.load_dataset')
    def test_load_mbpp_dataset_success(self, mock_load):
        """Test that load_mbpp_dataset returns the dataset object."""
        mock_load.return_value = mock_dataset_obj
        result = load_mbpp_dataset()
        assert result is not None
        mock_load.assert_called_once_with("mbpp", split="all", trust_remote_code=True)

    def test_save_raw_mbpp_files_creates_directory(self, tmp_path):
        """Test that save_raw_mbpp_files creates the output directory."""
        output_dir = tmp_path / "raw_mbpp"
        result = save_raw_mbpp_files(mock_dataset_obj, str(output_dir))
        
        assert output_dir.exists()
        assert len(result) == 1
        assert result[0].endswith("mbpp_raw.json")

    def test_save_raw_mbpp_files_content(self, tmp_path):
        """Test that the saved JSON file contains the correct data."""
        output_dir = tmp_path / "raw_mbpp"
        result = save_raw_mbpp_files(mock_dataset_obj, str(output_dir))
        
        file_path = Path(result[0])
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["task_id"] == 1
        assert data[1]["task_id"] == 2

    def test_save_raw_mbpp_files_invalid_dataset(self, tmp_path):
        """Test handling of a dataset that doesn't support to_list."""
        # Create a mock that behaves like a list of dicts directly
        class FakeDataset:
            def __iter__(self):
                return iter([{"task_id": 99}])
        
        output_dir = tmp_path / "raw_mbpp_fake"
        result = save_raw_mbpp_files(FakeDataset(), str(output_dir))
        
        assert len(result) == 1
        with open(result[0], 'r') as f:
            data = json.load(f)
        assert data[0]["task_id"] == 99
