"""
Unit tests for the download module (T034).

These tests verify that:
1. The download script logs the raw record count.
2. The download script does NOT halt on data insufficiency (delegates to T011).
3. No synthetic fallback is used when real data sources are unavailable.
"""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from download import (
    exponential_backoff_retry,
    fetch_materials_project_data,
    fetch_openkim_data,
    save_raw_data,
    main,
)
from utils import setup_logging, raise_data_insufficiency
from error_handling import DataInsufficiencyError


@pytest.fixture
def mock_logger():
    """Provide a mock logger for testing."""
    logger = MagicMock(spec=logging.Logger)
    with patch("download.logging.getLogger", return_value=logger):
        yield logger


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for raw data storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestExponentialBackoffRetry:
    """Tests for the exponential backoff retry logic."""

    def test_success_on_first_attempt(self):
        """Test that a successful function returns immediately."""
        func = MagicMock(return_value={"status": "success"})
        result = exponential_backoff_retry(func, max_retries=3)
        assert result == {"status": "success"}
        func.assert_called_once()

    def test_retry_on_failure(self):
        """Test that the function retries on failure."""
        func = MagicMock(side_effect=[ValueError("Rate limit"), {"status": "success"}])
        result = exponential_backoff_retry(func, max_retries=3, base_delay=0.01)
        assert result == {"status": "success"}
        assert func.call_count == 2

    def test_max_retries_exceeded(self):
        """Test that the function raises after max retries."""
        func = MagicMock(side_effect=ValueError("Persistent error"))
        with pytest.raises(ValueError):
            exponential_backoff_retry(func, max_retries=2, base_delay=0.01)


class TestFetchMaterialsProjectData:
    """Tests for Materials Project data fetching."""

    @patch("download.requests.get")
    def test_fetch_success(self, mock_get, mock_logger):
        """Test successful data fetch from Materials Project."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"task_id": "mp-123", "structure": {"atoms": []}},
                {"task_id": "mp-456", "structure": {"atoms": []}},
            ],
            "total_count": 2,
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"MP_API_KEY": "fake_key"}):
            result = fetch_materials_project_data()

        assert result is not None
        assert "data" in result
        assert len(result["data"]) == 2
        mock_logger.info.assert_any_call("Materials Project: Retrieved 2 raw records")

    @patch("download.requests.get")
    def test_fetch_failure_api_key_missing(self, mock_get, mock_logger):
        """Test that fetch fails gracefully when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = fetch_materials_project_data()

        assert result is None
        mock_logger.warning.assert_any_call("MP_API_KEY not found in environment variables.")

    @patch("download.requests.get")
    def test_fetch_failure_empty_response(self, mock_get, mock_logger):
        """Test handling of empty API response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [], "total_count": 0}
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"MP_API_KEY": "fake_key"}):
            result = fetch_materials_project_data()

        assert result is not None
        assert len(result["data"]) == 0
        mock_logger.info.assert_any_call("Materials Project: Retrieved 0 raw records")


class TestFetchOpenKIMData:
    """Tests for OpenKIM data fetching."""

    @patch("download.requests.get")
    def test_fetch_success(self, mock_get, mock_logger):
        """Test successful data fetch from OpenKIM."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "kim-123", "properties": {}},
                {"id": "kim-456", "properties": {}},
            ],
            "total": 2,
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"OPENKIM_API_KEY": "fake_key"}):
            result = fetch_openkim_data()

        assert result is not None
        assert "data" in result
        assert len(result["data"]) == 2
        mock_logger.info.assert_any_call("OpenKIM: Retrieved 2 raw records")

    @patch("download.requests.get")
    def test_fetch_failure_api_key_missing(self, mock_get, mock_logger):
        """Test that fetch skips when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = fetch_openkim_data()

        assert result is None
        mock_logger.warning.assert_any_call("OPENKIM_API_KEY not found. Skipping OpenKIM fetch.")


class TestSaveRawData:
    """Tests for saving raw data to disk."""

    def test_save_creates_files(self, temp_data_dir, mock_logger):
        """Test that save_raw_data creates files with checksums."""
        data = {"test": "data", "count": 10}
        source = "mp"
        record_id = "test-123"

        save_raw_data(data, source, record_id, temp_data_dir)

        expected_path = temp_data_dir / source / f"{record_id}.json"
        assert expected_path.exists()

        with open(expected_path, "r") as f:
            saved_data = json.load(f)

        assert saved_data == data
        mock_logger.info.assert_any_call(f"Saved {source}/{record_id}.json with checksum")

    def test_save_creates_directory(self, temp_data_dir, mock_logger):
        """Test that save_raw_data creates the source directory if needed."""
        data = {"test": "data"}
        source = "new_source"
        record_id = "test-456"

        save_raw_data(data, source, record_id, temp_data_dir)

        expected_dir = temp_data_dir / source
        assert expected_dir.exists()


class TestDataInsufficiencyHandling:
    """Tests for data insufficiency behavior (T034 core)."""

    def test_main_logs_count_but_does_not_halt_on_zero(self, mock_logger, temp_data_dir):
        """
        Verify that main() logs the raw count (even if 0) but does NOT
        raise DataInsufficiencyError here. The check is delegated to T011.
        """
        # Mock the fetch functions to return empty data
        with patch("download.fetch_materials_project_data", return_value={"data": [], "total_count": 0}):
            with patch("download.fetch_openkim_data", return_value={"data": [], "total_count": 0}):
                with patch("download.save_raw_data"):
                    # We need to mock raise_data_insufficiency to prevent actual exit
                    # but we want to verify it is NOT called in download.py
                    with patch("download.raise_data_insufficiency") as mock_raise:
                        try:
                            # Mock sys.exit to prevent actual exit if raise_data_insufficiency is called
                            with patch("sys.exit"):
                                main()
                        except SystemExit:
                            pass  # Expected if raise_data_insufficiency is called

                        # Verify that the logger was called with the count
                        mock_logger.info.assert_any_call("Total records retrieved: 0")

                        # CRITICAL: Verify that raise_data_insufficiency was NOT called
                        # The download script should NOT halt on insufficiency; T011 does that.
                        mock_raise.assert_not_called()

    def test_no_synthetic_fallback(self, mock_logger):
        """
        Verify that when real data sources fail, no synthetic/fake data
        is generated or returned. The function should return None or empty.
        """
        with patch("download.requests.get", side_effect=Exception("Network error")):
            with patch.dict(os.environ, {"MP_API_KEY": "fake_key"}):
                result = fetch_materials_project_data()

        assert result is None or (isinstance(result, dict) and len(result.get("data", [])) == 0)
        # Verify no synthetic data generation occurred
        mock_logger.warning.assert_any_call("Failed to fetch from Materials Project: Network error")


class TestIntegration:
    """Integration tests for the download pipeline."""

    def test_end_to_end_with_mocked_api(self, temp_data_dir, mock_logger):
        """Test the full download flow with mocked API responses."""
        mock_mp_data = {
            "data": [{"task_id": f"mp-{i}", "structure": {}} for i in range(5)],
            "total_count": 5,
        }
        mock_kim_data = {
            "data": [{"id": f"kim-{i}", "properties": {}} for i in range(3)],
            "total": 3,
        }

        with patch("download.fetch_materials_project_data", return_value=mock_mp_data):
            with patch("download.fetch_openkim_data", return_value=mock_kim_data):
                with patch("download.save_raw_data") as mock_save:
                    with patch("sys.exit"):
                        main()

                    # Verify save_raw_data was called for all records
                    assert mock_save.call_count == 8  # 5 MP + 3 KIM
                    mock_logger.info.assert_any_call("Total records retrieved: 8")

    def test_partial_failure_handling(self, temp_data_dir, mock_logger):
        """Test that partial failure (one source fails) does not crash the pipeline."""
        mock_mp_data = {
            "data": [{"task_id": "mp-1", "structure": {}}],
            "total_count": 1,
        }

        with patch("download.fetch_materials_project_data", return_value=mock_mp_data):
            with patch("download.fetch_openkim_data", return_value=None):
                with patch("download.save_raw_data") as mock_save:
                    with patch("sys.exit"):
                        main()

                    # Should save only MP data
                    assert mock_save.call_count == 1
                    mock_logger.warning.assert_any_call("OpenKIM: No data retrieved (API key missing or fetch failed).")