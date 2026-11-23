"""
Unit tests for src.data.download module.
Tests the GWOSC noise fetching functionality.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.data.download import fetch_gw_noise_segment, fetch_batch_noise_segments
from src.utils.config import get_project_root


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_gwosc_data():
    """Mock GWOSC data for testing."""
    # Create mock strain data
    num_samples = 4096 * 4096  # 4096 seconds at 1024 Hz
    times = np.arange(num_samples) / 1024.0
    strain = np.random.randn(num_samples) * 1e-23
    
    return {
        'times': times,
        'strain': strain,
        'sample_rate': 1024
    }


def test_fetch_gw_noise_segment_creates_file(temp_output_dir, mock_gwosc_data):
    """Test that fetch_gw_noise_segment creates a file."""
    with patch('src.data.download.datasets') as mock_datasets:
        # Mock the segment list
        mock_datasets.find_gwosc_segments.return_value = [(1234567890, 1234567890 + 4096)]
        
        # Mock the fetch_strain_data
        mock_datasets.fetch_strain_data.return_value = {
            'H1': {
                'times': mock_gwosc_data['times'],
                'strain': mock_gwosc_data['strain'],
                'sample_rate': mock_gwosc_data['sample_rate']
            }
        }
        
        result_path = fetch_gw_noise_segment(
            event_id="test_event",
            detector="H1",
            run="O4",
            output_dir=temp_output_dir
        )
        
        assert result_path is not None
        assert result_path.exists()
        assert result_path.suffix == '.hdf5'


def test_fetch_gw_noise_segment_skips_existing(temp_output_dir, mock_gwosc_data):
    """Test that fetch_gw_noise_segment skips existing files."""
    # Create a pre-existing file
    existing_path = temp_output_dir / "test_event_H1_O4.hdf5"
    existing_path.touch()
    
    with patch('src.data.download.datasets') as mock_datasets:
        # This should not be called because file exists
        result_path = fetch_gw_noise_segment(
            event_id="test_event",
            detector="H1",
            run="O4",
            output_dir=temp_output_dir
        )
        
        assert result_path == existing_path
        mock_datasets.fetch_strain_data.assert_not_called()


def test_fetch_batch_noise_segments(temp_output_dir, mock_gwosc_data):
    """Test batch fetching of noise segments."""
    with patch('src.data.download.datasets') as mock_datasets:
        # Mock the segment list
        mock_datasets.find_gwosc_segments.return_value = [(1234567890, 1234567890 + 4096)]
        
        # Mock the fetch_strain_data
        mock_datasets.fetch_strain_data.return_value = {
            'H1': {
                'times': mock_gwosc_data['times'],
                'strain': mock_gwosc_data['strain'],
                'sample_rate': mock_gwosc_data['sample_rate']
            }
        }
        
        event_ids = ["event1", "event2", "event3"]
        result_paths = fetch_batch_noise_segments(
            event_ids=event_ids,
            detector="H1",
            output_dir=temp_output_dir
        )
        
        assert len(result_paths) == len(event_ids)
        for path in result_paths:
            assert path.exists()


def test_fetch_gw_noise_segment_handles_errors(temp_output_dir):
    """Test that fetch_gw_noise_segment raises RuntimeError on failure."""
    with patch('src.data.download.datasets') as mock_datasets:
        # Simulate failure
        mock_datasets.find_gwosc_segments.side_effect = Exception("API Error")
        
        with pytest.raises(RuntimeError, match="Failed to fetch noise segment"):
            fetch_gw_noise_segment(
                event_id="test_event",
                detector="H1",
                run="O4",
                output_dir=temp_output_dir
            )


def test_constants_are_defined():
    """Test that required constants are defined."""
    from src.data.download import GWOSC_BASE_URL, TARGET_RUNS, DETECTORS, SEGMENT_DURATION
    
    assert GWOSC_BASE_URL == "https://www.gwosc.org"
    assert "O4" in TARGET_RUNS
    assert "H1" in DETECTORS
    assert SEGMENT_DURATION == 4096