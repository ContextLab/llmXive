"""
Unit tests for src.data.batch_processor (T015 logic).

Tests the loop condition: while valid_count < min_valid_events and attempts < max_attempts.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import os
import logging

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.batch_processor import process_batch, run_injection_campaign

# Mocks
def mock_fetch_noise(event_id, output_dir):
    """Mock a successful noise fetch."""
    # Create a dummy file
    path = output_dir / f"{event_id}_noise.h5"
    path.touch()
    return path

def mock_inject_signal(noise_path, output_path, true_params, logger):
    """Mock injection that always succeeds."""
    output_path.touch()
    # Create a dummy metadata file
    meta_path = output_path.with_suffix('.json')
    meta_path.write_text('{"true_parameters": {"mass": 30, "spin": 0.5}}')

def mock_validate_file(file_path):
    """Mock validation that always succeeds."""
    return True, {"snr": 10.0}

def mock_check_spin(file_path):
    """Mock spin check."""
    return True

@patch('src.data.batch_processor.fetch_gw_noise_segment', side_effect=mock_fetch_noise)
@patch('src.data.batch_processor.inject_synthetic_signal', side_effect=mock_inject_signal)
@patch('src.data.batch_processor.validate_file', side_effect=mock_validate_file)
@patch('src.data.batch_processor.check_true_parameters_exist', return_value=True)
def test_run_injection_campaign_stops_at_target(
    mock_check_spin, mock_validate, mock_inject, mock_fetch
):
    """Test that the campaign stops after finding 12 valid events."""
    with patch('pathlib.Path.mkdir'):
        valid_events, attempts, summary = run_injection_campaign(
            target_events=15,
            min_valid_events=12,
            max_attempts=20
        )
    
    assert len(valid_events) == 12
    assert attempts == 12  # Should stop exactly at 12
    assert summary["target_met"] is True

@patch('src.data.batch_processor.fetch_gw_noise_segment', side_effect=mock_fetch_noise)
@patch('src.data.batch_processor.inject_synthetic_signal', side_effect=mock_inject_signal)
@patch('src.data.batch_processor.validate_file', return_value=(False, {"error": "low snr"}))
@patch('src.data.batch_processor.check_true_parameters_exist', return_value=False)
def test_run_injection_campaign_raises_on_failure(
    mock_check_spin, mock_validate, mock_inject, mock_fetch
):
    """Test that the campaign raises an error if max attempts are reached without enough valid events."""
    with patch('pathlib.Path.mkdir'):
        with pytest.raises(RuntimeError) as exc_info:
            run_injection_campaign(
                target_events=15,
                min_valid_events=12,
                max_attempts=3  # Only 3 attempts, need 12
            )
        
        assert "Max attempts reached" in str(exc_info.value)