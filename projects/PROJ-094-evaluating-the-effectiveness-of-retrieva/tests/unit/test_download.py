"""
Unit tests for src/data/download.py
"""
import pytest
import os
import tempfile
from pathlib import Path
import json
from unittest.mock import patch, MagicMock, mock_open
import hashlib

# Mock ir_datasets before importing the module to be tested
# We need to mock the load function and the dataset iterator
import sys
from unittest.mock import MagicMock

# Create a mock ir_datasets module
mock_ir_datasets = MagicMock()
sys.modules['ir_datasets'] = mock_ir_datasets

# Now import the module under test
# We need to handle the path properly
import importlib.util
spec = importlib.util.spec_from_file_location("download", "src/data/download.py")
download_module = importlib.util.module_from_spec(spec)

# Mock the PROJECT_ROOT and directories to avoid file system dependency in unit tests
with patch.object(download_module, 'PROJECT_ROOT', Path(tempfile.gettempdir())):
    with patch.object(download_module, 'DATA_RAW_DIR', Path(tempfile.gettempdir()) / "test_raw"):
        with patch.object(download_module, 'TRAIN_DIR', Path(tempfile.gettempdir()) / "test_raw" / "train"):
            with patch.object(download_module, 'TEST_DIR', Path(tempfile.gettempdir()) / "test_raw" / "test"):
                spec.loader.exec_module(download_module)

from download_module import ensure_directories, download_and_save_subset, verify_download, load_dataset_subset


class TestEnsureDirectories:
    def test_ensure_directories_creates_folders(self, tmp_path):
        """Test that ensure_directories creates the necessary folder structure."""
        # Patch the global paths to use tmp_path
        with patch.object(download_module, 'DATA_RAW_DIR', tmp_path / "raw"):
            with patch.object(download_module, 'TRAIN_DIR', tmp_path / "raw" / "train"):
                with patch.object(download_module, 'TEST_DIR', tmp_path / "raw" / "test"):
                    download_module.ensure_directories()
                    
                    assert (tmp_path / "raw").exists()
                    assert (tmp_path / "raw" / "train").exists()
                    assert (tmp_path / "raw" / "test").exists()


class TestLoadDatasetSubset:
    def test_load_dataset_success(self):
        """Test successful loading of a dataset."""
        mock_dataset = MagicMock()
        mock_ir_datasets.load.return_value = mock_dataset

        result = download_module.load_dataset_subset("codesearchnet-python/train")
        
        mock_ir_datasets.load.assert_called_once_with("codesearchnet-python/train")
        assert result == mock_dataset

    def test_load_dataset_failure(self):
        """Test that load_dataset_subset raises RuntimeError on failure."""
        mock_ir_datasets.load.side_effect = Exception("Network error")

        with pytest.raises(RuntimeError, match="Failed to load dataset"):
            download_module.load_dataset_subset("codesearchnet-python/train")


class TestDownloadAndSaveSubset:
    @pytest.fixture
    def mock_dataset_items(self):
        """Fixture providing mock dataset items."""
        return [
            {"function_id": "1", "function_name": "add", "function_docstring": "Adds two numbers", "function_body": "return a + b"},
            {"function_id": "2", "function_name": "subtract", "function_docstring": "Subtracts two numbers", "function_body": "return a - b"}
        ]

    def test_download_and_save_subset(self, tmp_path, mock_dataset_items):
        """Test downloading and saving a subset."""
        output_dir = tmp_path / "train"
        output_dir.mkdir()

        # Mock the dataset
        mock_dataset = MagicMock()
        mock_dataset.__iter__ = MagicMock(return_value=iter(mock_dataset_items))
        mock_ir_datasets.load.return_value = mock_dataset

        result = download_module.download_and_save_subset(
            "codesearchnet-python/train",
            output_dir,
            "python_train"
        )

        # Check result
        assert result["status"] == "success"
        assert result["item_count"] == 2
        assert result["dataset_id"] == "codesearchnet-python/train"
        
        # Check file creation
        expected_file = output_dir / "python_train.jsonl"
        assert expected_file.exists()
        
        # Check content
        with open(expected_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 2
            data = json.loads(lines[0])
            assert data["function_name"] == "add"

    def test_download_and_save_subset_handles_exception(self, tmp_path):
        """Test that download_and_save_subset raises RuntimeError on failure."""
        output_dir = tmp_path / "train"
        output_dir.mkdir()

        mock_ir_datasets.load.side_effect = Exception("Download failed")

        with pytest.raises(RuntimeError, match="Failed to download"):
            download_module.download_and_save_subset(
                "codesearchnet-python/train",
                output_dir,
                "python_train"
            )


class TestVerifyDownload:
    def test_verify_download_success(self, tmp_path):
        """Test successful verification."""
        output_dir = tmp_path / "train"
        output_dir.mkdir()
        
        # Create a non-empty file
        (output_dir / "test.jsonl").write_text("line1\nline2")

        assert download_module.verify_download(output_dir) is True

    def test_verify_download_empty_file(self, tmp_path):
        """Test verification fails on empty file."""
        output_dir = tmp_path / "train"
        output_dir.mkdir()
        
        # Create an empty file
        (output_dir / "test.jsonl").write_text("")

        assert download_module.verify_download(output_dir) is False

    def test_verify_download_no_files(self, tmp_path):
        """Test verification fails if no files exist."""
        output_dir = tmp_path / "train"
        output_dir.mkdir()

        assert download_module.verify_download(output_dir) is False

    def test_verify_download_missing_directory(self, tmp_path):
        """Test verification fails if directory is missing."""
        output_dir = tmp_path / "nonexistent"

        assert download_module.verify_download(output_dir) is False


def test_no_synthetic_fallback_in_code():
    """
    Static analysis check to ensure no synthetic data generation or fallback 
    logic exists in the download module.
    """
    import inspect
    source = inspect.getsource(download_module)
    
    # Check for common patterns of synthetic data generation or fallback
    forbidden_patterns = [
        "generate_synthetic",
        "mock_data",
        "fake_data",
        "if .* fallback",
        "except.*:.*generate",
        "except.*:.*return.*mock",
        "np.random",
        "random.sample",
        "synthetic"
    ]
    
    for pattern in forbidden_patterns:
        # Simple string check, could be improved with regex
        if pattern.lower() in source.lower():
            # Allow comments that mention these as negatives
            lines = source.split('\n')
            for line in lines:
                if pattern.lower() in line.lower() and not line.strip().startswith('#'):
                    pytest.fail(f"Potential synthetic fallback or data generation found: {pattern} in line: {line}")
                    
    assert True, "No synthetic fallback patterns detected"
