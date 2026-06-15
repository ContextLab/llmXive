"""Unit tests for the knot atlas downloader module.

Tests verify:
- Exponential backoff retry logic (1s → 2s → 4s delays)
- Partial cache creation after 3 consecutive failures
- Timeout handling for network requests
"""

import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import pytest

from download.knot_atlas_loader import (
    KnotRecord,
    DownloadFailure,
    KnotAtlasDownloader,
    download_knot_atlas_data,
    verify_retry_logic,
    verify_partial_caching,
)


class TestRetryLogic:
    """Test exponential backoff retry logic."""

    @pytest.fixture
    def downloader(self, tmp_path):
        """Create a downloader instance with test cache directory."""
        return KnotAtlasDownloader(cache_dir=str(tmp_path))

    def test_download_retry_logic(self, downloader):
        """Verify exponential backoff delays 1s→2s→4s on simulated failures.

        This test mocks requests.get to fail on first 3 calls, then succeed.
        It verifies that:
        1. First retry waits ~1s (initial=1s)
        2. Second retry waits ~2s (multiplier=2)
        3. Third retry waits ~4s (multiplier=2)
        """
        call_count = [0]
        base_time = time.time()

        def mock_get_with_backoff(*args, **kwargs):
            """Mock requests.get that fails 3 times then succeeds."""
            call_count[0] += 1
            if call_count[0] <= 3:
                raise requests.exceptions.ConnectionError("Simulated failure")
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "knots": [
                    {
                        "crossing_number": 3,
                        "braid_index": 2,
                        "hyperbolic_volume": 0.5,
                        "is_alternating": True,
                    }
                ]
            }
            mock_response.raise_for_status = MagicMock()
            return mock_response

        import requests

        with patch("download.knot_atlas_loader.requests.get", side_effect=mock_get_with_backoff):
            # Record timing of each retry attempt
            with patch("download.knot_atlas_loader.time.sleep") as mock_sleep:
                # Call download - should trigger retries
                result = downloader.download_knots(max_crossing=3)

                # Verify sleep was called with exponential backoff delays
                # Expected: 1s, 2s, 4s (after failures 1, 2, 3)
                expected_delays = [1.0, 2.0, 4.0]
                actual_delays = [call[0][0] for call in mock_sleep.call_args_list]

                # Verify delays match exponential backoff pattern
                assert len(actual_delays) == 3, f"Expected 3 retry delays, got {len(actual_delays)}"

                for i, (expected, actual) in enumerate(zip(expected_delays, actual_delays)):
                    # Allow 10% tolerance for timing variations
                    tolerance = expected * 0.1
                    assert abs(actual - expected) <= tolerance, (
                        f"Retry {i+1}: expected delay {expected}s, got {actual}s"
                    )

                # Verify download eventually succeeded
                assert result is not None
                assert len(result) > 0

    def test_download_retry_logic_uses_verify_retry_logic(self, downloader):
        """Verify verify_retry_logic function works correctly."""
        # Create mock failure scenarios
        def failing_get(*args, **kwargs):
            raise requests.exceptions.ConnectionError("Simulated failure")

        import requests

        with patch("download.knot_atlas_loader.requests.get", side_effect=failing_get):
            # Verify the verification function catches failures
            with patch("download.knot_atlas_loader.time.sleep"):
                with pytest.raises(Exception):
                    verify_retry_logic(
                        url="https://example.com/test",
                        max_retries=3,
                        initial_delay=1.0,
                        max_delay=32.0,
                        multiplier=2.0,
                    )


class TestPartialCache:
    """Test partial cache creation after consecutive failures."""

    @pytest.fixture
    def downloader(self, tmp_path):
        """Create a downloader instance with test cache directory."""
        return KnotAtlasDownloader(cache_dir=str(tmp_path))

    def test_download_partial_cache(self, downloader):
        """Verify cache creation after 3 consecutive failures.

        This test mocks requests.get to always fail, then verifies:
        1. A partial cache file is created after 3 consecutive failures
        2. The cache file contains partial download state
        """
        import requests

        def mock_get_always_fail(*args, **kwargs):
            """Mock requests.get that always fails."""
            raise requests.exceptions.ConnectionError("Simulated persistent failure")

        with patch("download.knot_atlas_loader.requests.get", side_effect=mock_get_always_fail):
            with patch("download.knot_atlas_loader.time.sleep"):
                # Attempt download - should fail and create partial cache
                result = downloader.download_knots(max_crossing=3)

                # Verify partial cache was created
                cache_path = Path(downloader.cache_dir)
                partial_files = list(cache_path.glob("*partial*"))

                assert len(partial_files) > 0, (
                    f"Expected partial cache file, but found none in {cache_path}"
                )

                # Verify cache file contains expected metadata
                partial_file = partial_files[0]
                with open(partial_file, "r") as f:
                    cache_data = json.load(f)

                assert "status" in cache_data
                assert cache_data["status"] == "partial"
                assert "error" in cache_data or "error_count" in cache_data

    def test_download_partial_cache_uses_verify_partial_caching(self, downloader):
        """Verify verify_partial_caching function works correctly."""
        import requests

        def mock_get_fail(*args, **kwargs):
            raise requests.exceptions.ConnectionError("Simulated failure")

        with patch("download.knot_atlas_loader.requests.get", side_effect=mock_get_fail):
            with patch("download.knot_atlas_loader.time.sleep"):
                # Verify the verification function can detect partial cache
                cache_path = Path(downloader.cache_dir)
                cache_path.mkdir(parents=True, exist_ok=True)

                # Create a mock partial cache file
                partial_file = cache_path / "partial_test.json"
                with open(partial_file, "w") as f:
                    json.dump({"status": "partial", "error_count": 3}, f)

                result = verify_partial_caching(str(cache_path))
                assert result is not None
                assert "partial" in result or "status" in result


class TestTimeoutHandling:
    """Test timeout handling for network requests."""

    @pytest.fixture
    def downloader(self, tmp_path):
        """Create a downloader instance with test cache directory."""
        return KnotAtlasDownloader(cache_dir=str(tmp_path), timeout=5)

    def test_download_timeout(self, downloader):
        """Verify timeout handling for network requests.

        This test mocks requests.get to raise a timeout exception, then verifies:
        1. The timeout exception is properly caught
        2. Appropriate error handling occurs
        3. Partial cache or error logging occurs
        """
        import requests

        def mock_get_timeout(*args, **kwargs):
            """Mock requests.get that raises timeout."""
            raise requests.exceptions.Timeout("Simulated timeout")

        with patch("download.knot_atlas_loader.requests.get", side_effect=mock_get_timeout):
            with patch("download.knot_atlas_loader.time.sleep"):
                # Attempt download with timeout - should handle gracefully
                result = downloader.download_knots(max_crossing=3)

                # Verify result is None or empty due to timeout
                assert result is None or len(result) == 0

                # Verify error was logged or cache was created
                cache_path = Path(downloader.cache_dir)
                cache_files = list(cache_path.glob("*"))

                # Either partial cache exists or we can verify timeout was handled
                assert len(cache_files) > 0 or result is None

    def test_download_timeout_with_retry(self, downloader):
        """Verify timeout triggers retry logic."""
        import requests

        call_count = [0]

        def mock_get_timeout_with_retry(*args, **kwargs):
            """Mock requests.get that times out then succeeds."""
            call_count[0] += 1
            if call_count[0] <= 2:
                raise requests.exceptions.Timeout("Simulated timeout")
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "knots": [
                    {
                        "crossing_number": 3,
                        "braid_index": 2,
                        "hyperbolic_volume": 0.5,
                        "is_alternating": True,
                    }
                ]
            }
            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch("download.knot_atlas_loader.requests.get", side_effect=mock_get_timeout_with_retry):
            with patch("download.knot_atlas_loader.time.sleep") as mock_sleep:
                result = downloader.download_knots(max_crossing=3)

                # Verify retry was attempted
                assert call_count[0] > 1

                # Verify sleep was called (backoff)
                assert mock_sleep.call_count > 0

                # Verify eventual success
                assert result is not None
                assert len(result) > 0


class TestKnotRecordValidation:
    """Test KnotRecord dataclass and validation."""

    def test_knot_record_creation(self):
        """Verify KnotRecord can be created with required fields."""
        record = KnotRecord(
            crossing_number=3,
            braid_index=2,
            hyperbolic_volume=0.5,
            is_alternating=True,
        )

        assert record.crossing_number == 3
        assert record.braid_index == 2
        assert record.hyperbolic_volume == 0.5
        assert record.is_alternating is True

    def test_knot_record_dict_conversion(self):
        """Verify KnotRecord can be converted to dict."""
        record = KnotRecord(
            crossing_number=3,
            braid_index=2,
            hyperbolic_volume=0.5,
            is_alternating=True,
        )

        record_dict = record.asdict()
        assert isinstance(record_dict, dict)
        assert "crossing_number" in record_dict
        assert "braid_index" in record_dict
        assert "hyperbolic_volume" in record_dict
        assert "is_alternating" in record_dict

    def test_download_failure_creation(self):
        """Verify DownloadFailure can be created."""
        failure = DownloadFailure(
            error_type="ConnectionError",
            error_message="Test error",
            retry_count=3,
        )

        assert failure.error_type == "ConnectionError"
        assert failure.error_message == "Test error"
        assert failure.retry_count == 3
