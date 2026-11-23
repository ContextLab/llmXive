"""
Unit tests for src/compression/main.py (T022).
"""
import pytest
import os
import sys
import json
import tempfile
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.compression.main import load_validated_event, process_single_event, main
from src.utils.config import get_project_root, ensure_dir

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_event_data():
    """Create mock event data."""
    return {
        "event_id": "test_event_001",
        "waveform": np.sin(np.linspace(0, 10 * np.pi, 1000)).tolist(),
        "snr": 12.5,
        "true_parameters": {
            "mass": 30.0,
            "distance": 100.0,
            "tilt_angle": 0.5
        }
    }

def test_load_validated_event_not_found(temp_output_dir):
    """Test loading a non-existent event."""
    result = load_validated_event("non_existent_event")
    assert result is None

@patch('src.compression.main.load_validated_event')
def test_process_single_event_missing_waveform(mock_load, temp_output_dir, mock_event_data):
    """Test processing an event with missing waveform."""
    mock_load.return_value = {"event_id": "test", "waveform": None}
    result = process_single_event("test", temp_output_dir)
    assert result["status"] == "failed"
    assert "Missing waveform" in result["error"]

@patch('src.compression.main.load_validated_event')
@patch('src.compression.main.compute_compression_metrics')
@patch('src.compression.main.ensure_dir')
def test_process_single_event_success(mock_ensure, mock_metrics, mock_load, temp_output_dir, mock_event_data):
    """Test successful processing of a single event."""
    mock_load.return_value = mock_event_data
    mock_metrics.return_value = {
        "mse": 0.001,
        "snr_degradation_db": 2.5,
        "status": "acceptable"
    }
    
    result = process_single_event("test_event_001", temp_output_dir)
    
    assert result["event_id"] == "test_event_001"
    assert "compression_results" in result
    assert len(result["compression_results"]) > 0

@patch('src.compression.main.process_single_event')
@patch('src.compression.main.load_validated_event')
@patch('builtins.open', new_callable=MagicMock)
def test_main_successful_run(mock_open, mock_load, mock_process, temp_output_dir, mock_event_data):
    """Test the main function with successful processing."""
    # Setup mock for valid_events.json
    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps({
        "event_ids": ["event1", "event2"],
        "count": 2
    })
    
    mock_load.return_value = mock_event_data
    mock_process.return_value = {
        "event_id": "event1",
        "compression_results": [{"method": "lossless", "algorithm": "gzip", "status": "success"}]
    }
    
    # Mock get_project_root to return temp directory
    with patch('src.compression.main.get_project_root', return_value=temp_output_dir):
        result = main()
        
    assert result == 0

@patch('src.compression.main.process_single_event')
@patch('builtins.open', new_callable=MagicMock)
def test_main_with_failed_events(mock_open, mock_process, temp_output_dir):
    """Test main function with some failed events."""
    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps({
        "event_ids": ["event1", "event2"],
        "count": 2
    })
    
    mock_process.side_effect = [
        {"event_id": "event1", "status": "success", "compression_results": []},
        {"event_id": "event2", "status": "failed", "error": "Test error"}
    ]
    
    with patch('src.compression.main.get_project_root', return_value=temp_output_dir):
        result = main()
        
    # Should exit with error code if any events failed
    assert result == 1