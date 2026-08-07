"""
Unit tests for the Robust Data Fetcher (T010).
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

import pytest

# Mock the datasets import before importing download.py to avoid dependency issues in CI
# unless the test environment actually has it installed.
try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False

from data.download import download_benchmark_dataset, main
from config import DATA_RAW

@pytest.mark.skipif(not HAS_DATASETS, reason="datasets library not installed")
class TestDownload:
    def test_download_creates_file(self, tmp_path):
        """
        Test that the download function creates the expected output file.
        Note: This test mocks the load_dataset call to avoid network dependency,
        but verifies the file writing logic.
        """
        # Create a mock dataset iterator
        mock_data = [
            {"id": "1", "problem": "test", "solution": "print(1)"},
            {"id": "2", "problem": "test2", "solution": "print(2)"}
        ]

        with patch("data.download.load_dataset") as mock_load:
            mock_load.return_value = iter(mock_data)

            output_file = download_benchmark_dataset(tmp_path)

            assert output_file.exists()
            assert output_file.name == "bench.final.public.jsonl"

            # Verify content
            with open(output_file, "r") as f:
                lines = f.readlines()
            assert len(lines) == 2
            assert "test" in lines[0]
            assert "test2" in lines[1]

    def test_download_handles_empty_dataset(self, tmp_path):
        """Test behavior with an empty dataset."""
        with patch("data.download.load_dataset") as mock_load:
            mock_load.return_value = iter([])

            output_file = download_benchmark_dataset(tmp_path)

            assert output_file.exists()
            assert output_file.stat().st_size == 0

    def test_download_raises_on_connection_error(self, tmp_path):
        """Test that ConnectionError is raised if fetching fails."""
        with patch("data.download.load_dataset") as mock_load:
            mock_load.side_effect = Exception("Network timeout")

            with pytest.raises(ConnectionError):
                download_benchmark_dataset(tmp_path)

    def test_download_ensures_directory_exists(self, tmp_path):
        """Test that the output directory is created if missing."""
        nested_dir = tmp_path / "sub" / "nested"
        assert not nested_dir.exists()

        mock_data = [{"id": "1"}]
        with patch("data.download.load_dataset") as mock_load:
            mock_load.return_value = iter(mock_data)
            download_benchmark_dataset(nested_dir)

        assert nested_dir.exists()
        assert (nested_dir / "bench.final.public.jsonl").exists()

def test_main_return_code_on_success(capsys):
    """Test that main returns 0 on success (mocked)."""
    mock_data = [{"id": "1"}]
    with patch("data.download.load_dataset") as mock_load:
        mock_load.return_value = iter(mock_data)
        with patch("data.download.get_path", return_value=Path(tempfile.gettempdir())):
            exit_code = main()
            assert exit_code == 0

def test_main_return_code_on_failure(capsys):
    """Test that main returns 1 on failure."""
    with patch("data.download.load_dataset") as mock_load:
        mock_load.side_effect = Exception("Failed")
        with patch("data.download.get_path", return_value=Path(tempfile.gettempdir())):
            exit_code = main()
            assert exit_code == 1
            captured = capsys.readouterr()
            assert "Failed" in captured.err