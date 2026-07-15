"""
Unit tests for the batch processing logic (T015).
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import os

# Add code directory to path
code_path = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from src.data.batch_processor import process_batch, run_injection_campaign


@pytest.fixture
def mock_fetch_noise():
    with patch("src.data.batch_processor.fetch_gw_noise_segment") as mock:
        mock.return_value = ("data/raw/mock_noise.h5", {"detector": "H1", "time": 12345})
        yield mock


@pytest.fixture
def mock_inject_signal():
    with patch("src.data.batch_processor.inject_synthetic_signal") as mock:
        mock.return_value = ("data/interim/injected/mock_injected.h5", {"true_parameters": {"mass": 30}})
        yield mock


@pytest.fixture
def mock_validate_file():
    with patch("src.data.batch_processor.validate_file") as mock:
        mock.return_value = (True, {"detector": "H1", "valid": True})
        yield mock


@pytest.fixture
def mock_check_spin():
    with patch("src.data.batch_processor.check_true_parameters_exist") as mock:
        mock.return_value = True
        yield mock


def test_process_batch_finds_valid_events(
    mock_fetch_noise,
    mock_inject_signal,
    mock_validate_file,
    mock_check_spin
):
    """Test that process_batch correctly identifies and returns valid events."""
    valid_events, attempts = process_batch(batch_size=3)

    assert len(valid_events) == 3
    assert attempts == 3
    mock_fetch_noise.assert_called()
    mock_inject_signal.assert_called()
    mock_validate_file.assert_called()
    mock_check_spin.assert_called()


def test_process_batch_skips_invalid_spin(
    mock_fetch_noise,
    mock_inject_signal,
    mock_validate_file,
    mock_check_spin
):
    """Test that process_batch skips events missing spin metadata."""
    # Make the third event fail spin check
    mock_check_spin.side_effect = [True, True, False]

    valid_events, attempts = process_batch(batch_size=3)

    assert len(valid_events) == 2
    assert attempts == 3


def test_run_injection_campaign_stops_at_target(
    mock_fetch_noise,
    mock_inject_signal,
    mock_validate_file,
    mock_check_spin
):
    """Test that run_injection_campaign stops once target is reached."""
    # Mock process_batch to return 5 valid events each time
    with patch("src.data.batch_processor.process_batch") as mock_process:
        mock_process.return_value = (
            [{"id": i} for i in range(5)],
            5
        )

        result = run_injection_campaign(target_valid_count=12, batch_size=5, max_batches=10)

        # We need 3 batches to get 15 events (>= 12)
        # 1st batch: 5 total
        # 2nd batch: 10 total
        # 3rd batch: 15 total -> Stop
        assert len(result) >= 12
        assert mock_process.call_count == 3


def test_run_injection_campaign_raises_on_failure():
    """Test that run_injection_campaign raises RuntimeError if target not met."""
    with patch("src.data.batch_processor.process_batch") as mock_process:
        # Return 0 valid events every time
        mock_process.return_value = ([], 5)

        with pytest.raises(RuntimeError, match="Failed to find"):
            run_injection_campaign(target_valid_count=12, batch_size=5, max_batches=2)
