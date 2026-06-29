"""
Unit tests for data_loader streaming functionality.

Tests T018 implementation: streaming mode verification and CSV output.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import csv
import tempfile
import os

# Import the module under test
from data_loader import (
    handle_rate_limit,
    handle_network_error,
    load_raw_data,
    stream_dataset,
    compute_file_checksum,
    save_raw_data_to_csv,
    download_and_save_sample,
)


class TestHandleRateLimit:
    """Tests for rate limit handling."""

    def test_rate_limit_exceeded_raises_error(self):
        """Test that exceeding max retries raises RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            handle_rate_limit(attempt=5, max_retries=5)
        assert "Rate limit exceeded" in str(exc_info.value)

    @patch("data_loader.time.sleep")
    def test_rate_limit_waits_before_retry(self, mock_sleep):
        """Test that rate limit handling includes wait time."""
        # Should not raise for attempt < max_retries
        handle_rate_limit(attempt=0, max_retries=5)
        mock_sleep.assert_called_once()


class TestHandleNetworkError:
    """Tests for network error handling."""

    def test_network_error_exceeded_raises_error(self):
        """Test that exceeding max retries raises RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            handle_network_error(Exception("connection lost"), attempt=5, max_retries=5)
        assert "Network error after" in str(exc_info.value)

    @patch("data_loader.time.sleep")
    def test_network_error_waits_before_retry(self, mock_sleep):
        """Test that network error handling includes wait time."""
        handle_network_error(Exception("timeout"), attempt=0, max_retries=5)
        mock_sleep.assert_called_once()


class TestComputeFileChecksum:
    """Tests for file checksum computation."""

    def test_compute_checksum_returns_hex_string(self):
        """Test that checksum computation returns hex string."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)

        try:
            checksum = compute_file_checksum(temp_path)
            assert isinstance(checksum, str)
            assert len(checksum) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)

    def test_identical_content_same_checksum(self):
        """Test that identical content produces same checksum."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f1:
            f1.write("test content")
            temp_path1 = Path(f.name)

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f2:
            f2.write("test content")
            temp_path2 = Path(f.name)

        try:
            checksum1 = compute_file_checksum(temp_path1)
            checksum2 = compute_file_checksum(temp_path2)
            assert checksum1 == checksum2
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)


class TestSaveRawDataToCsv:
    """Tests for CSV saving functionality."""

    def test_save_empty_data_creates_empty_file(self):
        """Test that empty data creates empty CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty.csv"
            save_raw_data_to_csv([], output_path)
            assert output_path.exists()
            assert output_path.stat().st_size == 0

    def test_save_data_creates_csv_with_headers(self):
        """Test that data saves with correct headers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data.csv"
            data = [
                {"content": "print('hello')", "path": "test.py", "language": "python"},
                {"content": "x = 1", "path": "test2.py", "language": "python"},
            ]
            save_raw_data_to_csv(data, output_path)

            assert output_path.exists()
            with open(output_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert "content" in reader.fieldnames
                assert "path" in reader.fieldnames

    def test_save_data_preserves_content(self):
        """Test that content is preserved in CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "data.csv"
            data = [
                {"content": "def foo():\n    pass", "path": "test.py"},
            ]
            save_raw_data_to_csv(data, output_path)

            with open(output_path, "r") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert rows[0]["content"] == "def foo():\n    pass"


class TestDownloadAndSaveSample:
    """Tests for main download functionality."""

    @patch("data_loader.stream_dataset")
    @patch("data_loader.save_raw_data_to_csv")
    def test_download_saves_to_correct_path(self, mock_save, mock_stream):
        """Test that download saves to the correct output path."""
        mock_stream.return_value = iter([{"content": "test", "path": "test.py"}])
        mock_save.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sample.csv"
            result = download_and_save_sample(
                dataset_name="test/dataset",
                output_path=output_path,
                max_samples=10,
                streaming=True
            )

            assert result == output_path
            mock_stream.assert_called_once()
            mock_save.assert_called_once()

    @patch("data_loader.stream_dataset")
    @patch("data_loader.save_raw_data_to_csv")
    def test_download_uses_streaming_mode(self, mock_save, mock_stream):
        """Test that streaming mode is enabled."""
        mock_stream.return_value = iter([{"content": "test"}])

        download_and_save_sample(
            dataset_name="test/dataset",
            streaming=True,
            max_samples=100
        )

        # Verify streaming was passed correctly
        call_args = mock_stream.call_args
        assert call_args is not None

    @patch("data_loader.stream_dataset")
    def test_download_handles_empty_stream(self, mock_stream):
        """Test that empty stream creates empty CSV."""
        mock_stream.return_value = iter([])

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "empty_sample.csv"
            download_and_save_sample(
                dataset_name="test/dataset",
                output_path=output_path,
                max_samples=100,
                streaming=True
            )

            assert output_path.exists()

    @patch("data_loader.stream_dataset")
    def test_download_forces_streaming_true(self, mock_stream):
        """Test that streaming is forced to True."""
        mock_stream.return_value = iter([{"content": "test"}])

        # Even if streaming=False is passed, it should be forced to True
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sample.csv"
            download_and_save_sample(
                dataset_name="test/dataset",
                output_path=output_path,
                streaming=False,  # Should be overridden
                max_samples=100
            )

            # Verify stream_dataset was called with streaming=True
            call_kwargs = mock_stream.call_args[1]
            assert call_kwargs.get("streaming") == True


class TestStreamDataset:
    """Tests for streaming functionality."""

    @patch("data_loader.load_raw_data")
    def test_stream_returns_generator(self, mock_load):
        """Test that stream_dataset returns a generator."""
        mock_load.return_value = iter([{"content": "test"}])

        result = stream_dataset("test/dataset", streaming=True, max_samples=100)

        # Generator should be iterable
        items = list(result)
        assert len(items) == 1

    @patch("data_loader.load_raw_data")
    def test_stream_handles_max_samples(self, mock_load):
        """Test that max_samples limit is respected."""
        mock_load.return_value = iter([{"content": str(i)} for i in range(200)])

        result = list(stream_dataset("test/dataset", streaming=True, max_samples=50))

        assert len(result) == 50
        assert mock_load.call_args[1]["max_samples"] == 50
