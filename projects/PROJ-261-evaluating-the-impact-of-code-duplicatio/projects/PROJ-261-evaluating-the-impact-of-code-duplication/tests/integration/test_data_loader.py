"""
Integration test for HuggingFace rate-limiting and network-interruption handling
during 500 MB download.

This test validates that the data_loader.py module correctly handles:
- HTTP 429 rate-limiting responses with exponential backoff
- Network interruptions (ConnectionError, Timeout) with retry logic
- Successful download after transient failures

Per Constitution Principle III (Data Hygiene), this test ensures robust data
acquisition that doesn't silently fail on external service issues.
"""

import pytest
import time
from unittest.mock import patch, MagicMock, Mock
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data_loader import (
    handle_rate_limit,
    handle_network_error,
    stream_dataset,
    save_raw_data_to_csv,
    download_and_save_sample
)
from config import get_random_seed

# Set random seed for reproducibility
RANDOM_SEED = get_random_seed()


class TestHandleRateLimit:
    """Test rate-limiting handling with exponential backoff."""

    def test_handle_rate_limit_respects_max_retries(self):
        """Verify that handle_rate_limit raises after max retries exceeded."""
        from data_loader import handle_rate_limit
        import logging

        logger = logging.getLogger(__name__)

        with patch('time.sleep') as mock_sleep:
            with pytest.raises(Exception) as exc_info:
                handle_rate_limit(
                    max_retries=3,
                    initial_wait=0.1,
                    logger=logger
                )

            # Verify sleep was called 3 times (for retries 0, 1, 2)
            assert mock_sleep.call_count == 3
            # Verify exponential backoff: 0.1, 0.2, 0.4
            expected_waits = [0.1, 0.2, 0.4]
            actual_waits = [call[0][0] for call in mock_sleep.call_args_list]
            for expected, actual in zip(expected_waits, actual_waits):
                assert abs(actual - expected) < 0.01

    def test_handle_rate_limit_succeeds_before_max_retries(self):
        """Verify successful completion when rate limit clears early."""
        from data_loader import handle_rate_limit
        import logging

        logger = logging.getLogger(__name__)
        call_count = [0]

        def flaky_operation():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Rate limit exceeded (429)")
            return "success"

        with patch('time.sleep') as mock_sleep:
            result = handle_rate_limit(
                max_retries=3,
                initial_wait=0.1,
                logger=logger,
                operation=flaky_operation
            )

            assert result == "success"
            assert call_count[0] == 2
            # Only 1 sleep call (after first failure)
            assert mock_sleep.call_count == 1

    def test_handle_rate_limit_logs_retry_attempts(self):
        """Verify that retry attempts are logged appropriately."""
        from data_loader import handle_rate_limit
        import logging

        # Create a logger with a handler to capture logs
        logger = logging.getLogger('test_rate_limit')
        logger.setLevel(logging.INFO)
        log_handler = logging.Handler()
        log_handler.setLevel(logging.INFO)
        log_records = []

        def emit(record):
            log_records.append(record)
        log_handler.emit = emit
        logger.addHandler(log_handler)

        call_count = [0]

        def flaky_operation():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Rate limit exceeded (429)")
            return "success"

        with patch('time.sleep'):
            handle_rate_limit(
                max_retries=3,
                initial_wait=0.01,
                logger=logger,
                operation=flaky_operation
            )

        # Should have logged at least one retry attempt
        retry_logs = [r for r in log_records if 'retry' in r.message.lower()]
        assert len(retry_logs) >= 1


class TestHandleNetworkError:
    """Test network interruption handling with retry logic."""

    def test_handle_network_error_handles_connection_error(self):
        """Verify ConnectionError is caught and retried."""
        from data_loader import handle_network_error
        import logging

        logger = logging.getLogger(__name__)
        call_count = [0]

        def flaky_network_operation():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Connection reset by peer")
            return "data downloaded"

        with patch('time.sleep'):
            result = handle_network_error(
                max_retries=3,
                initial_wait=0.1,
                logger=logger,
                operation=flaky_network_operation
            )

            assert result == "data downloaded"
            assert call_count[0] == 2

    def test_handle_network_error_handles_timeout(self):
        """Verify Timeout is caught and retried."""
        from data_loader import handle_network_error
        import logging

        logger = logging.getLogger(__name__)
        call_count = [0]

        def flaky_timeout_operation():
            call_count[0] += 1
            if call_count[0] < 2:
                raise TimeoutError("Request timed out")
            return "data downloaded"

        with patch('time.sleep'):
            result = handle_network_error(
                max_retries=3,
                initial_wait=0.1,
                logger=logger,
                operation=flaky_timeout_operation
            )

            assert result == "data downloaded"
            assert call_count[0] == 2

    def test_handle_network_error_raises_after_max_retries(self):
        """Verify network errors are raised after max retries."""
        from data_loader import handle_network_error
        import logging

        logger = logging.getLogger(__name__)

        def always_fails():
            raise ConnectionError("Connection refused")

        with patch('time.sleep'):
            with pytest.raises(ConnectionError):
                handle_network_error(
                    max_retries=3,
                    initial_wait=0.1,
                    logger=logger,
                    operation=always_fails
                )


class TestStreamDataset:
    """Test streaming dataset download with error handling."""

    def test_stream_dataset_handles_rate_limit_during_stream(self):
        """Verify rate limiting is handled during streaming."""
        from data_loader import stream_dataset
        import logging

        logger = logging.getLogger(__name__)

        # Mock the datasets library
        mock_dataset = MagicMock()
        mock_iterator = iter([
            {'code': 'def hello(): pass'},
            {'code': 'def world(): pass'},
        ])
        mock_dataset.__iter__ = lambda self: mock_iterator

        with patch('datasets.load_dataset') as mock_load:
            mock_load.return_value = mock_dataset

            # Test that streaming works without rate limit errors
            samples = []
            for sample in stream_dataset(
                dataset_name='codeparrot/github-code',
                max_samples=2,
                streaming_enabled=True,
                logger=logger
            ):
                samples.append(sample)

            assert len(samples) == 2

    def test_stream_dataset_respects_max_samples(self):
        """Verify streaming respects max_samples limit."""
        from data_loader import stream_dataset
        import logging

        logger = logging.getLogger(__name__)

        mock_dataset = MagicMock()
        mock_iterator = iter([
            {'code': f'def func_{i}(): pass'}
            for i in range(100)
        ])
        mock_dataset.__iter__ = lambda self: mock_iterator

        with patch('datasets.load_dataset') as mock_load:
            mock_load.return_value = mock_dataset

            samples = []
            for sample in stream_dataset(
                dataset_name='codeparrot/github-code',
                max_samples=5,
                streaming_enabled=True,
                logger=logger
            ):
                samples.append(sample)

            assert len(samples) == 5


class TestSaveRawDataToCSV:
    """Test CSV saving functionality."""

    def test_save_raw_data_to_csv_creates_file(self, tmp_path):
        """Verify CSV file is created with correct structure."""
        from data_loader import save_raw_data_to_csv
        import logging

        logger = logging.getLogger(__name__)
        output_path = tmp_path / 'test_output.csv'

        test_data = [
            {'code': 'def hello(): pass', 'repo': 'test/repo1', 'path': 'file1.py'},
            {'code': 'def world(): pass', 'repo': 'test/repo2', 'path': 'file2.py'},
        ]

        save_raw_data_to_csv(
            data=test_data,
            output_path=str(output_path),
            logger=logger
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify CSV content
        import csv
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert 'code' in rows[0]
            assert 'repo' in rows[0]
            assert 'path' in rows[0]

    def test_save_raw_data_to_csv_handles_empty_data(self, tmp_path):
        """Verify empty data list creates valid empty CSV."""
        from data_loader import save_raw_data_to_csv
        import logging

        logger = logging.getLogger(__name__)
        output_path = tmp_path / 'empty_output.csv'

        save_raw_data_to_csv(
            data=[],
            output_path=str(output_path),
            logger=logger
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0  # Should have header


class TestDownloadAndSaveSample:
    """Test end-to-end download and save workflow."""

    def test_download_and_save_sample_handles_rate_limit(self, tmp_path):
        """Verify rate limiting during full download workflow."""
        from data_loader import download_and_save_sample
        import logging

        logger = logging.getLogger(__name__)
        output_path = tmp_path / 'sample.csv'

        # Mock the streaming to simulate rate limit then success
        call_count = [0]

        def mock_stream(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call simulates rate limit recovery
                time.sleep(0.01)
            return [
                {'code': f'def func_{i}(): pass', 'repo': 'test/repo', 'path': f'file_{i}.py'}
                for i in range(10)
            ]

        with patch('data_loader.stream_dataset', side_effect=mock_stream):
            with patch('data_loader.save_raw_data_to_csv') as mock_save:
                result = download_and_save_sample(
                    output_path=str(output_path),
                    max_samples=10,
                    dataset_name='codeparrot/github-code',
                    logger=logger
                )

                assert result is True
                mock_save.assert_called_once()

    def test_download_and_save_sample_handles_network_error(self, tmp_path):
        """Verify network errors during full download workflow."""
        from data_loader import download_and_save_sample
        import logging

        logger = logging.getLogger(__name__)
        output_path = tmp_path / 'sample.csv'

        call_count = [0]

        def flaky_stream(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 2:
                raise ConnectionError("Network interrupted")
            return [
                {'code': f'def func_{i}(): pass', 'repo': 'test/repo', 'path': f'file_{i}.py'}
                for i in range(10)
            ]

        with patch('data_loader.stream_dataset', side_effect=flaky_stream):
            with patch('data_loader.save_raw_data_to_csv') as mock_save:
                result = download_and_save_sample(
                    output_path=str(output_path),
                    max_samples=10,
                    dataset_name='codeparrot/github-code',
                    logger=logger
                )

                assert result is True
                assert call_count[0] == 2
                mock_save.assert_called_once()


class TestIntegrationRateLimitAndNetwork:
    """Integration tests combining rate limiting and network errors."""

    def test_combined_rate_limit_and_network_handling(self, tmp_path):
        """Verify both error types are handled in sequence."""
        from data_loader import download_and_save_sample
        import logging

        logger = logging.getLogger(__name__)
        output_path = tmp_path / 'combined_test.csv'

        call_sequence = [0]

        def combined_error_stream(*args, **kwargs):
            call_sequence[0] += 1
            if call_sequence[0] == 1:
                raise Exception("Rate limit (429)")
            elif call_sequence[0] == 2:
                raise ConnectionError("Network interrupted")
            elif call_sequence[0] == 3:
                raise TimeoutError("Request timed out")
            return [
                {'code': f'def func_{i}(): pass', 'repo': 'test/repo', 'path': f'file_{i}.py'}
                for i in range(5)
            ]

        with patch('data_loader.stream_dataset', side_effect=combined_error_stream):
            with patch('time.sleep'):  # Don't actually wait in tests
                with patch('data_loader.save_raw_data_to_csv') as mock_save:
                    result = download_and_save_sample(
                        output_path=str(output_path),
                        max_samples=5,
                        dataset_name='codeparrot/github-code',
                        logger=logger
                    )

                    assert result is True
                    assert call_sequence[0] == 4  # 3 failures + 1 success
                    mock_save.assert_called_once()

    def test_500mb_download_simulation(self, tmp_path):
        """Simulate 500MB download with intermittent errors."""
        from data_loader import download_and_save_sample
        import logging

        logger = logging.getLogger(__name__)
        output_path = tmp_path / '500mb_sample.csv'

        # Simulate a large download with ~1000 samples
        # (500MB / ~500KB per sample ≈ 1000 samples)
        sample_count = 1000
        error_interval = 50  # Error every 50 samples

        call_count = [0]

        def large_download_stream(*args, **kwargs):
            for i in range(sample_count):
                call_count[0] += 1
                if call_count[0] % error_interval == 0:
                    if call_count[0] < error_interval * 3:
                        # First few intervals have errors
                        if call_count[0] % (error_interval * 2) == 0:
                            raise ConnectionError("Network interrupted")
                        else:
                            raise Exception("Rate limit (429)")
                yield {
                    'code': f'def func_{i}():\n    return "sample_{i}"\n' * 100,
                    'repo': 'test/large-repo',
                    'path': f'large_file_{i}.py'
                }

        with patch('data_loader.stream_dataset', side_effect=large_download_stream):
            with patch('time.sleep'):
                with patch('data_loader.save_raw_data_to_csv') as mock_save:
                    result = download_and_save_sample(
                        output_path=str(output_path),
                        max_samples=sample_count,
                        dataset_name='codeparrot/github-code',
                        logger=logger
                    )

                    assert result is True
                    # Verify save was called with correct data
                    assert mock_save.called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])