"""
Tests for the download module.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to mock the config to avoid modifying the real project state during tests
# but we also need to test the actual logic. We will patch the DATA_RAW_DIR.
from unittest.mock import patch, mock_open, MagicMock

from code.download import download_human_eval, HUMAN_EVAL_URL, OUTPUT_PATH

class TestDownloadHumanEval:
    def test_ensure_directory_created(self, tmp_path):
        """Test that the function creates the data/raw directory if it doesn't exist."""
        # Create a temporary directory to act as DATA_RAW_DIR
        test_raw_dir = tmp_path / "data" / "raw"
        assert not test_raw_dir.exists()

        # Mock the requests.get to return a successful response with fake data
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_content = MagicMock(return_value=[b'{"test": "data"}\n'])

        with patch("code.download.requests.get", return_value=mock_response):
            with patch("code.download.DATA_RAW_DIR", str(test_raw_dir)):
                # Temporarily update OUTPUT_PATH logic inside the function via environment or direct patch
                # Since the function uses the module-level constant, we patch the module's constant
                with patch("code.download.OUTPUT_PATH", str(test_raw_dir / "human_eval_data.jsonl")):
                    result = download_human_eval()

        assert result is True
        assert test_raw_dir.exists()
        assert (test_raw_dir / "human_eval_data.jsonl").exists()

    def test_download_success(self, tmp_path):
        """Test successful download and file creation."""
        test_raw_dir = tmp_path / "data" / "raw"
        test_file = test_raw_dir / "human_eval_data.jsonl"
        
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        # Simulate a JSONL response
        mock_response.iter_content = MagicMock(return_value=[b'{"problem_id": 1}\n', b'{"problem_id": 2}\n'])

        with patch("code.download.requests.get", return_value=mock_response):
            with patch("code.download.DATA_RAW_DIR", str(test_raw_dir)):
                with patch("code.download.OUTPUT_PATH", str(test_file)):
                    result = download_human_eval()

        assert result is True
        assert test_file.exists()
        
        # Verify content
        with open(test_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["problem_id"] == 1
        assert json.loads(lines[1])["problem_id"] == 2

    def test_download_failure_raises_exception(self):
        """Test that a network error raises an exception."""
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(side_effect=Exception("Network Error"))
        
        with patch("code.download.requests.get", return_value=mock_response):
            with pytest.raises(Exception):
                download_human_eval()
