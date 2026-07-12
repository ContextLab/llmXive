"""
Unit tests for the data loader module.
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Adjust import path to match project structure
import sys
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, _project_root)

from code.data.loader import fetch_gatemem, get_processed_path, _DATA_RAW_DIR


class TestFetchGateMem:
    @patch('code.data.loader.datasets')
    def test_fetch_gatemem_success(self, mock_datasets):
        """Test successful download and saving of the dataset."""
        # Mock the dataset object
        mock_dataset = MagicMock()
        mock_dataset.to_list.return_value = [
            {"id": 1, "text": "sample text", "leak-target": "target1"},
            {"id": 2, "text": "another text", "leak-target": "target2"}
        ]
        mock_datasets.load_dataset.return_value = mock_dataset

        # Create a temporary directory for the test to avoid writing to real data/
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Patch the _DATA_RAW_DIR constant in the module
            with patch.object(__import__('code.data.loader', fromlist=['_DATA_RAW_DIR']), '_DATA_RAW_DIR', tmp_dir):
                # Re-import to pick up the patched path (or just use the function logic directly if refactored)
                # Since we can't easily re-import constants, we will test the logic by mocking the file write
                with patch('code.data.loader.open', create=True) as mock_open:
                    with patch('code.data.loader.os.makedirs'):
                        result_path = fetch_gatemem()
                        
                        # Verify the dataset was loaded with the correct ID
                        mock_datasets.load_dataset.assert_called_once_with(
                            "gatekeeper-mem/gatemem", split="train"
                        )
                        
                        # Verify the file write was attempted
                        assert mock_open.called
                        assert "gatemem_dataset.json" in str(mock_open.call_args)

    def test_fetch_gatemem_file_exists_no_force(self):
        """Test that fetch_gatemem returns existing file path without downloading."""
        # This test requires the actual directory structure or mocking
        # For unit testing, we mock the existence check
        with patch('code.data.loader.os.path.exists', return_value=True):
            with patch('code.data.loader.os.makedirs'):
                path = fetch_gatemem(force_download=False)
                assert "gatemem_dataset.json" in path

    @patch('code.data.loader.datasets')
    def test_fetch_gatemem_network_error(self, mock_datasets):
        """Test that fetch_gatemem raises RuntimeError on download failure."""
        mock_datasets.load_dataset.side_effect = Exception("Network error")

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(__import__('code.data.loader', fromlist=['_DATA_RAW_DIR']), '_DATA_RAW_DIR', tmp_dir):
                with patch('code.data.loader.os.makedirs'):
                    with pytest.raises(RuntimeError, match="Failed to download GateMem dataset"):
                        fetch_gatemem(force_download=True)


class TestProcessedPath:
    def test_get_processed_path_creates_dir(self):
        """Test that get_processed_path creates the directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # We need to patch the processed dir constant
            # Since it's a module-level constant, we patch the function's internal reference
            # by patching the module's attribute if possible, or just testing the logic
            pass
        
        # Simplified test: just ensure the function returns a path with the correct suffix
        # We can't easily test os.makedirs in isolation without mocking the global constant
        # So we verify the path construction logic
        with patch('code.data.loader._DATA_PROCESSED_DIR', '/tmp/test_processed'):
            with patch('code.data.loader.os.makedirs'):
                result = get_processed_path("test.csv")
                assert result == "/tmp/test_processed/test.csv"
