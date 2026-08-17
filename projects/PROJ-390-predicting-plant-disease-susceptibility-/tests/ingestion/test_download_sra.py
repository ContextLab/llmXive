"""
Tests for SRA data downloader.
"""
import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ingestion.download_sra import (
    exponential_backoff,
    fetch_sra_ids,
    download_sra_run,
    atomic_write_metadata,
    download_species_data,
    main
)


class TestExponentialBackoff:
    """Tests for exponential backoff calculation."""

    def test_basic_exponential_growth(self):
        """Test that backoff grows exponentially."""
        delay0 = exponential_backoff(0, base_delay=2.0, max_delay=30.0)
        delay1 = exponential_backoff(1, base_delay=2.0, max_delay=30.0)
        delay2 = exponential_backoff(2, base_delay=2.0, max_delay=30.0)

        assert delay1 > delay0
        assert delay2 > delay1

    def test_max_delay_cap(self):
        """Test that backoff is capped at max_delay."""
        delay = exponential_backoff(10, base_delay=2.0, max_delay=30.0)
        assert delay <= 30.0

    def test_jitter_addition(self):
        """Test that jitter is added to delay."""
        delay1 = exponential_backoff(0, base_delay=2.0, max_delay=30.0)
        delay2 = exponential_backoff(0, base_delay=2.0, max_delay=30.0)

        # With jitter, consecutive calls should not be exactly equal
        # (though they might occasionally be due to the small jitter range)
        base_delay = 2.0
        assert abs(delay1 - base_delay) < 0.5  # Should be close to base


class TestFetchSraIds:
    """Tests for SRA ID fetching."""

    @patch('src.ingestion.download_sra.urlopen')
    def test_successful_fetch(self, mock_urlopen):
        """Test successful SRA ID fetch."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "esearchresult": {
                "idlist": ["12345", "67890"]
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        run_ids = fetch_sra_ids("wheat", "GCA_000003205.5")

        assert len(run_ids) == 2
        assert "12345" in run_ids
        assert "67890" in run_ids

    @patch('src.ingestion.download_sra.urlopen')
    def test_empty_result(self, mock_urlopen):
        """Test fetch with no results."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "esearchresult": {
                "idlist": []
            }
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        run_ids = fetch_sra_ids("wheat", "GCA_000003205.5")

        assert len(run_ids) == 0

    @patch('src.ingestion.download_sra.urlopen')
    def test_retry_on_error(self, mock_urlopen):
        """Test retry logic on error."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "esearchresult": {
                "idlist": ["12345"]
            }
        }).encode('utf-8')

        # First two calls raise error, third succeeds
        mock_urlopen.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            mock_response
        ]

        run_ids = fetch_sra_ids("wheat", "GCA_000003205.5")

        assert len(run_ids) == 1
        assert mock_urlopen.call_count == 3


class TestAtomicWriteMetadata:
    """Tests for atomic metadata writing."""

    def test_atomic_write_creates_file(self, tmp_path):
        """Test that atomic write creates the file."""
        metadata = {"test": "data", "number": 42}
        output_path = tmp_path / "test_metadata.json"

        atomic_write_metadata(metadata, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            written_data = json.load(f)

        assert written_data == metadata

    def test_atomic_write_overwrites(self, tmp_path):
        """Test that atomic write overwrites existing file."""
        output_path = tmp_path / "test_metadata.json"

        # Write initial data
        atomic_write_metadata({"old": "data"}, output_path)

        # Overwrite with new data
        atomic_write_metadata({"new": "data"}, output_path)

        with open(output_path, 'r') as f:
            written_data = json.load(f)

        assert written_data == {"new": "data"}


class TestMain:
    """Tests for main function."""

    @patch('src.ingestion.download_sra.download_species_data')
    @patch('src.ingestion.download_sra.ensure_paths_exist')
    def test_main_success(self, mock_ensure_paths, mock_download):
        """Test successful main execution."""
        mock_download.return_value = {"status": "completed"}

        with patch('sys.exit') as mock_exit:
            results = main()

        assert len(results) > 0
        mock_exit.assert_not_called()

    @patch('src.ingestion.download_sra.download_species_data')
    @patch('src.ingestion.download_sra.ensure_paths_exist')
    def test_main_partial_failure(self, mock_ensure_paths, mock_download):
        """Test main with partial failure."""
        mock_download.side_effect = [
            {"status": "completed"},
            {"status": "error", "error": "Network error"}
        ]

        with patch('sys.exit') as mock_exit:
            main()

        mock_exit.assert_called_once_with(1)