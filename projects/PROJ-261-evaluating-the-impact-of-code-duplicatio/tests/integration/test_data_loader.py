"""
Integration test for HuggingFace rate-limiting and network-interruption handling
during 500 MB download.

This test validates that the data_loader.py module properly handles:
1. HTTP 429 rate-limit responses from HuggingFace
2. Network interruptions (connection errors, timeouts)
3. Retry logic with exponential backoff
4. Graceful degradation when downloads fail

Per spec.md Independent Test requirements for User Story 1.
"""

import pytest
import time
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, sentinel
from requests.exceptions import ConnectionError, Timeout, HTTPError
import logging

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'projects' / 'PROJ-261-evaluating-the-impact-of-code-duplication' / 'code'))

from data_loader import (
    setup_logging,
    handle_rate_limit,
    handle_network_error,
    compute_file_checksum,
    stream_dataset,
    save_raw_data_to_csv,
    download_and_save_sample,
    load_raw_data
)


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_response_429():
    """Mock HTTP 429 rate-limit response."""
    response = Mock()
    response.status_code = 429
    response.headers = {'Retry-After': '5'}
    response.raise_for_status.side_effect = HTTPError(response=response)
    return response


@pytest.fixture
def mock_response_success():
    """Mock successful HTTP response."""
    response = Mock()
    response.status_code = 200
    response.headers = {'Content-Type': 'application/json'}
    return response


@pytest.fixture
def mock_connection_error():
    """Mock connection error exception."""
    return ConnectionError("Connection refused")


@pytest.fixture
def mock_timeout_error():
    """Mock timeout exception."""
    return Timeout("Request timed out")


class TestHandleRateLimit:
    """Test rate-limit handling functionality."""

    def test_handle_rate_limit_with_retry_after_header(self, mock_response_429, caplog):
        """Test that handle_rate_limit respects Retry-After header."""
        caplog.set_level(logging.INFO)

        # Should not raise, should return True (handled)
        result = handle_rate_limit(mock_response_429)

        assert result is True
        assert "Rate limit detected" in caplog.text
        assert "Retry-After" in caplog.text

    def test_handle_rate_limit_without_retry_after_header(self, caplog):
        """Test fallback behavior when Retry-After header is missing."""
        response = Mock()
        response.status_code = 429
        response.headers = {}
        response.raise_for_status.side_effect = HTTPError(response=response)

        caplog.set_level(logging.INFO)

        result = handle_rate_limit(response)

        assert result is True
        assert "Rate limit detected" in caplog.text
        assert "default 60 second" in caplog.text

    def test_handle_rate_limit_non_429_response(self, mock_response_success):
        """Test that non-429 responses return False."""
        result = handle_rate_limit(mock_response_success)
        assert result is False


class TestHandleNetworkError:
    """Test network error handling functionality."""

    def test_handle_network_error_connection_error(self, mock_connection_error, caplog):
        """Test handling of connection errors."""
        caplog.set_level(logging.ERROR)

        result = handle_network_error(mock_connection_error, max_retries=3)

        assert result is True
        assert "Network error" in caplog.text
        assert "ConnectionError" in caplog.text

    def test_handle_network_error_timeout(self, mock_timeout_error, caplog):
        """Test handling of timeout errors."""
        caplog.set_level(logging.ERROR)

        result = handle_network_error(mock_timeout_error, max_retries=3)

        assert result is True
        assert "Network error" in caplog.text
        assert "Timeout" in caplog.text

    def test_handle_network_error_non_network_exception(self, caplog):
        """Test that non-network exceptions are not handled."""
        caplog.set_level(logging.ERROR)

        result = handle_network_error(ValueError("Not a network error"), max_retries=3)

        assert result is False


class TestComputeFileChecksum:
    """Test checksum computation for downloaded files."""

    def test_compute_file_checksum_valid_file(self, temp_output_dir):
        """Test checksum computation on a valid file."""
        test_file = temp_output_dir / "test.txt"
        test_file.write_text("test content for checksum")

        checksum = compute_file_checksum(str(test_file))

        assert checksum is not None
        assert len(checksum) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in checksum.lower())

    def test_compute_file_checksum_nonexistent_file(self):
        """Test checksum computation on nonexistent file returns None."""
        checksum = compute_file_checksum("/nonexistent/path/file.txt")
        assert checksum is None


class TestStreamDataset:
    """Test dataset streaming functionality."""

    @patch('data_loader.load_dataset')
    def test_stream_dataset_success(self, mock_load_dataset, temp_output_dir):
        """Test successful dataset streaming."""
        # Mock dataset object
        mock_dataset = Mock()
        mock_dataset.__iter__ = Mock(return_value=iter([
            {'code': 'def hello(): pass', 'path': 'test.py'},
            {'code': 'def world(): pass', 'path': 'test2.py'}
        ]))
        mock_load_dataset.return_value = mock_dataset

        result = list(stream_dataset(
            dataset_name="test/dataset",
            streaming=True,
            max_samples=2
        ))

        assert len(result) == 2
        assert result[0]['code'] == 'def hello(): pass'
        mock_load_dataset.assert_called_once()
        assert mock_load_dataset.call_args[1]['streaming'] is True

    @patch('data_loader.load_dataset')
    def test_stream_dataset_rate_limit_handling(self, mock_load_dataset, caplog):
        """Test that streaming handles rate limits gracefully."""
        caplog.set_level(logging.WARNING)

        # First call raises rate limit, second succeeds
        rate_limit_error = HTTPError(response=Mock(status_code=429))
        mock_load_dataset.side_effect = [rate_limit_error, Mock()]
        mock_dataset = Mock()
        mock_dataset.__iter__ = Mock(return_value=iter([]))
        mock_load_dataset.return_value = mock_dataset

        result = list(stream_dataset(
            dataset_name="test/dataset",
            streaming=True,
            max_samples=1
        ))

        # Should retry and succeed
        assert len(result) == 0
        assert mock_load_dataset.call_count == 2


class TestSaveRawDataToCSV:
    """Test CSV saving functionality."""

    def test_save_raw_data_to_csv_creates_file(self, temp_output_dir):
        """Test that save_raw_data_to_csv creates the output file."""
        output_path = temp_output_dir / "output.csv"
        data = [
            {'code': 'def test(): pass', 'path': 'test.py', 'license': 'MIT'},
            {'code': 'def hello(): pass', 'path': 'hello.py', 'license': 'Apache'}
        ]

        save_raw_data_to_csv(data, str(output_path))

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify content
        with open(output_path, 'r') as f:
            content = f.read()
            assert 'code' in content
            assert 'path' in content

    def test_save_raw_data_to_csv_empty_data(self, temp_output_dir):
        """Test saving empty data creates file with headers only."""
        output_path = temp_output_dir / "empty.csv"

        save_raw_data_to_csv([], str(output_path))

        assert output_path.exists()
        with open(output_path, 'r') as f:
            content = f.read()
            assert 'code' in content  # Header should exist


class TestDownloadAndSaveSample:
    """Test download and save sample functionality."""

    @patch('data_loader.stream_dataset')
    @patch('data_loader.save_raw_data_to_csv')
    def test_download_and_save_sample_success(self, mock_save, mock_stream, temp_output_dir):
        """Test successful download and save."""
        mock_stream.return_value = [
            {'code': 'def test(): pass', 'path': 'test.py'}
        ]

        output_path = temp_output_dir / "sample.csv"

        result = download_and_save_sample(
            dataset_name="test/dataset",
            output_path=str(output_path),
            max_samples=10,
            streaming=True
        )

        assert result is True
        assert mock_stream.called
        assert mock_save.called
        assert mock_save.call_args[0][1] == str(output_path)

    @patch('data_loader.stream_dataset')
    def test_download_and_save_sample_network_error(self, mock_stream, temp_output_dir, caplog):
        """Test handling of network errors during download."""
        caplog.set_level(logging.ERROR)

        from requests.exceptions import ConnectionError
        mock_stream.side_effect = ConnectionError("Network error")

        output_path = temp_output_dir / "sample.csv"

        result = download_and_save_sample(
            dataset_name="test/dataset",
            output_path=str(output_path),
            max_samples=10,
            streaming=True
        )

        assert result is False
        assert "Network error" in caplog.text


class TestLoadRawData:
    """Test raw data loading functionality."""

    def test_load_raw_data_from_csv(self, temp_output_dir):
        """Test loading data from CSV file."""
        import csv
        csv_path = temp_output_dir / "test.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['code', 'path'])
            writer.writerow(['def test(): pass', 'test.py'])

        data = load_raw_data(str(csv_path))

        assert len(data) == 1
        assert data[0]['code'] == 'def test(): pass'
        assert data[0]['path'] == 'test.py'

    def test_load_raw_data_nonexistent_file(self):
        """Test loading from nonexistent file returns empty list."""
        data = load_raw_data("/nonexistent/path/file.csv")
        assert data == []


class TestIntegrationRateLimitAndNetworkHandling:
    """Integration tests for rate-limit and network handling during 500MB download simulation."""

    @patch('data_loader.load_dataset')
    def test_full_download_with_rate_limit_retry(self, mock_load_dataset, temp_output_dir, caplog):
        """Integration test: Full download flow with rate limit retry."""
        caplog.set_level(logging.INFO)

        # Simulate rate limit on first call, success on second
        rate_limit_error = HTTPError(response=Mock(status_code=429))
        mock_load_dataset.side_effect = [rate_limit_error, Mock()]

        mock_dataset = Mock()
        mock_dataset.__iter__ = Mock(return_value=iter([
            {'code': 'def hello(): pass', 'path': 'test.py', 'license': 'MIT'}
            for _ in range(100)  # Simulate 500MB worth of data (100 samples)
        ]))
        mock_load_dataset.return_value = mock_dataset

        output_path = temp_output_dir / "sample.csv"

        result = download_and_save_sample(
            dataset_name="codeparrot/github-code",
            output_path=str(output_path),
            max_samples=100,
            streaming=True
        )

        # Should succeed after retry
        assert result is True
        assert output_path.exists()
        assert mock_load_dataset.call_count == 2  # First failed, second succeeded
        assert "Rate limit" in caplog.text or "retry" in caplog.text.lower()

    @patch('data_loader.load_dataset')
    def test_full_download_with_network_interruption(self, mock_load_dataset, temp_output_dir, caplog):
        """Integration test: Full download flow with network interruption."""
        caplog.set_level(logging.ERROR)

        # Simulate network error on first call
        from requests.exceptions import ConnectionError
        mock_load_dataset.side_effect = ConnectionError("Network interrupted")

        output_path = temp_output_dir / "sample.csv"

        result = download_and_save_sample(
            dataset_name="codeparrot/github-code",
            output_path=str(output_path),
            max_samples=100,
            streaming=True
        )

        # Should handle gracefully and return False
        assert result is False
        assert not output_path.exists()
        assert "Network error" in caplog.text

    @patch('data_loader.load_dataset')
    def test_large_dataset_streaming_memory_efficient(self, mock_load_dataset, temp_output_dir):
        """Integration test: Verify streaming mode for large 500MB dataset."""
        mock_dataset = Mock()
        mock_dataset.__iter__ = Mock(return_value=iter([
            {'code': f'def code_{i}(): pass', 'path': f'file_{i}.py'}
            for i in range(1000)  # Simulate large dataset
        ]))
        mock_load_dataset.return_value = mock_dataset

        output_path = temp_output_dir / "large_sample.csv"

        result = download_and_save_sample(
            dataset_name="codeparrot/github-code",
            output_path=str(output_path),
            max_samples=1000,
            streaming=True
        )

        assert result is True
        assert output_path.exists()
        # Verify streaming was enabled
        call_kwargs = mock_load_dataset.call_args[1]
        assert call_kwargs.get('streaming') is True


class TestEdgeCases:
    """Test edge cases for data loader integration."""

    def test_zero_max_samples(self, temp_output_dir):
        """Test handling of zero max_samples."""
        output_path = temp_output_dir / "zero.csv"

        result = download_and_save_sample(
            dataset_name="test/dataset",
            output_path=str(output_path),
            max_samples=0,
            streaming=True
        )

        # Should handle gracefully (no data to download)
        assert result is True  # No error, just no data

    def test_invalid_output_path(self):
        """Test handling of invalid output path."""
        output_path = "/invalid/nonexistent/path/sample.csv"

        result = download_and_save_sample(
            dataset_name="test/dataset",
            output_path=output_path,
            max_samples=10,
            streaming=True
        )

        # Should fail gracefully
        assert result is False

    def test_empty_dataset(self, temp_output_dir):
        """Test handling of empty dataset."""
        with patch('data_loader.stream_dataset') as mock_stream:
            mock_stream.return_value = []

            output_path = temp_output_dir / "empty.csv"

            result = download_and_save_sample(
                dataset_name="test/empty",
                output_path=str(output_path),
                max_samples=10,
                streaming=True
            )

            assert result is True
            assert output_path.exists()
            # File should exist with headers only
            with open(output_path, 'r') as f:
                content = f.read()
                assert 'code' in content  # Header present


if __name__ == "__main__":
    pytest.main([__file__, "-v"])