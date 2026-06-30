"""Unit tests for the KnotAtlas downloader, focusing on exponential back-off behavior.

These tests verify that the exponential back-off retry logic in
`code/download/knot_atlas_loader.py` behaves correctly:
- Delays follow the sequence: initial * (multiplier ^ attempt)
- The delay is capped at a maximum value.
- The function raises an exception after exhausting retries.
- Partial caching is triggered after consecutive failures.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable
from unittest import mock

import pytest

from code.download.knot_atlas_loader import (
    download_knot_atlas_data,
    _fetch_with_backoff,
)


# Configuration constants matching the implementation
INITIAL_DELAY = 1.0
MULTIPLIER = 2
MAX_DELAY = 32.0
MAX_RETRIES = 3


@pytest.fixture
def mock_time_sleep():
    """Patch time.sleep to avoid actual delays during tests."""
    with mock.patch("code.download.knot_atlas_loader.time.sleep") as mock_sleep:
        yield mock_sleep


def test_backoff_delays_follow_sequence(mock_time_sleep):
    """Verify that delays follow the exponential sequence: 1s, 2s, 4s, capped at 32s."""
    call_delays = []

    def record_delay(delay: float) -> None:
        call_delays.append(delay)

    mock_time_sleep.side_effect = record_delay

    # Simulate a function that always fails
    def failing_func() -> None:
        raise ConnectionError("Simulated network failure")

    with pytest.raises(ConnectionError):
        _fetch_with_backoff(
            failing_func,
            initial_delay=INITIAL_DELAY,
            multiplier=MULTIPLIER,
            max_delay=MAX_DELAY,
            max_retries=MAX_RETRIES,
        )

    # Expected delays: 1, 2, 4 (capped at 32, but 4 < 32)
    expected_delays = [
        INITIAL_DELAY * (MULTIPLIER ** i)
        for i in range(MAX_RETRIES)
    ]
    # Cap at max_delay
    expected_delays = [min(d, MAX_DELAY) for d in expected_delays]

    assert call_delays == expected_delays, (
        f"Expected delays {expected_delays}, got {call_delays}"
    )


def test_backoff_caps_at_max_delay(mock_time_sleep):
    """Verify that delays are capped at max_delay."""
    call_delays = []

    def record_delay(delay: float) -> None:
        call_delays.append(delay)

    mock_time_sleep.side_effect = record_delay

    # Simulate a function that always fails
    def failing_func() -> None:
        raise ConnectionError("Simulated network failure")

    # Use a smaller max_retries to test capping
    test_max_retries = 6  # 1, 2, 4, 8, 16, 32 (capped)
    with pytest.raises(ConnectionError):
        _fetch_with_backoff(
            failing_func,
            initial_delay=INITIAL_DELAY,
            multiplier=MULTIPLIER,
            max_delay=MAX_DELAY,
            max_retries=test_max_retries,
        )

    # Expected delays: 1, 2, 4, 8, 16, 32 (capped)
    expected_delays = [
        min(INITIAL_DELAY * (MULTIPLIER ** i), MAX_DELAY)
        for i in range(test_max_retries)
    ]

    assert call_delays == expected_delays, (
        f"Expected capped delays {expected_delays}, got {call_delays}"
    )


def test_backoff_retries_exhausted_raises_exception(mock_time_sleep):
    """Verify that after max_retries, the original exception is raised."""
    call_count = 0

    def failing_func() -> None:
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Simulated network failure")

    with pytest.raises(ConnectionError, match="Simulated network failure"):
        _fetch_with_backoff(
            failing_func,
            initial_delay=INITIAL_DELAY,
            multiplier=MULTIPLIER,
            max_delay=MAX_DELAY,
            max_retries=MAX_RETRIES,
        )

    # Should be called initial attempt + max_retries retries
    assert call_count == MAX_RETRIES + 1, (
        f"Expected {MAX_RETRIES + 1} calls, got {call_count}"
    )


def test_backoff_succeeds_on_retry(mock_time_sleep):
    """Verify that the function returns successfully if the operation succeeds on a retry."""
    call_count = 0

    def eventually_succeeds() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("Simulated transient failure")
        return "Success"

    result = _fetch_with_backoff(
        eventually_succeeds,
        initial_delay=INITIAL_DELAY,
        multiplier=MULTIPLIER,
        max_delay=MAX_DELAY,
        max_retries=MAX_RETRIES,
    )

    assert result == "Success"
    assert call_count == 3
    # Should have slept twice (after attempt 1 and 2)
    assert mock_time_sleep.call_count == 2


def test_partial_cache_triggered_on_consecutive_failures(tmp_path: Path):
    """Verify that partial caching is triggered after consecutive failures."""
    cache_file = tmp_path / "partial_cache.json"
    call_count = 0

    def always_fails() -> None:
        nonlocal call_count
        call_count += 1
        raise ConnectionError("Simulated persistent failure")

    # Mock the _save_partial_cache function to verify it's called
    with mock.patch(
        "code.download.knot_atlas_loader._save_partial_cache"
    ) as mock_save_cache:
        mock_save_cache.return_value = None

        with pytest.raises(ConnectionError):
            _fetch_with_backoff(
                always_fails,
                initial_delay=INITIAL_DELAY,
                multiplier=MULTIPLIER,
                max_delay=MAX_DELAY,
                max_retries=MAX_RETRIES,
                cache_file=cache_file,
            )

        # Verify _save_partial_cache was called after the failure threshold
        # (typically after 3 consecutive failures as per FR-008)
        assert mock_save_cache.call_count >= 1, (
            "Expected partial cache to be saved after consecutive failures"
        )