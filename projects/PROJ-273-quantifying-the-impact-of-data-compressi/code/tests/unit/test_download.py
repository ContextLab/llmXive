"""
Unit tests for the download module.

These tests verify that the download functionality works correctly
with mock data and handles edge cases appropriately.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
import h5py

# Add the code directory to the path for imports
import sys
from tests.conftest import add_code_to_path
add_code_to_path()

from src.data.download import (
    fetch_gw_noise_segment,
    fetch_batch_noise_segments,
    DEFAULT_EVENTS,
    DETECTORS,
    SEGMENT_DURATION,
    SAMPLE_RATE
)

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def mock_gwosc_data():
    """Create mock GWOSC data."""
    # Create mock time series data
    sample_rate = SAMPLE_RATE
    duration = SEGMENT_DURATION
    n_samples = int(sample_rate * duration)
    
    # Create mock strain data (white noise)
    np.random.seed(42)
    strain_data = np.random.randn(n_samples)
    time_data = np.linspace(0, duration, n_samples)
    
    return {
        'strain': strain_data,
        'time': time_data,
        'gps_time': 1126259462.0,
        'event_name': 'GW150914',
        'detector': 'L1'
    }

def test_fetch_gw_noise_segment_creates_file(temp_output_dir, mock_gwosc_data):
    """Test that fetch_gw_noise_segment creates a valid HDF5 file."""
    # Mock the GWOSC API calls
    with patch('src.data.download.event_gps') as mock_gps, \
         patch('src.data.download.datarange') as mock_datarange, \
         patch('src.data.download.fetch_url') as mock_fetch:
        
        # Setup mocks
        mock_gps.return_value = mock_gwosc_data['gps_time']
        
        # Create a mock dataset object
        mock_ds = MagicMock()
        mock_ds.trange = (
            mock_gwosc_data['gps_time'] - 20,
            mock_gwosc_data['gps_time'] + 20
        )
        mock_datarange.return_value = [mock_ds]
        
        # Setup fetch_url to return mock data
        mock_fetch.return_value = {
            'L1': mock_gwosc_data['strain']
        }
        
        # Call the function
        result_path = fetch_gw_noise_segment(
            event_name='GW150914',
            detector='L1',
            output_dir=temp_output_dir
        )
        
        # Verify file was created
        assert result_path is not None
        assert result_path.exists()
        assert result_path.suffix == '.h5'
        
        # Verify file contents
        with h5py.File(result_path, 'r') as f:
            assert 'strain' in f
            assert 'time' in f
            assert f.attrs['event_name'] == 'GW150914'
            assert f.attrs['detector'] == 'L1'
            assert f.attrs['gps_time'] == mock_gwosc_data['gps_time']
            assert f.attrs['sample_rate'] == SAMPLE_RATE
            
            # Verify data shape
            assert f['strain'].shape[0] == len(mock_gwosc_data['strain'])

def test_fetch_gw_noise_segment_skips_existing(temp_output_dir, mock_gwosc_data):
    """Test that existing files are not re-downloaded."""
    # Create a dummy file first
    output_path = temp_output_dir / "GW150914_L1_noise.h5"
    output_path.touch()
    
    with patch('src.data.download.event_gps') as mock_gps:
        mock_gps.side_effect = Exception("Should not be called")
        
        result_path = fetch_gw_noise_segment(
            event_name='GW150914',
            detector='L1',
            output_dir=temp_output_dir
        )
        
        # Verify the same path was returned and no API calls were made
        assert result_path == output_path

def test_fetch_batch_noise_segments(temp_output_dir, mock_gwosc_data):
    """Test batch fetching functionality."""
    events = ['GW150914', 'GW151012']
    detectors = ['L1', 'H1']
    
    with patch('src.data.download.event_gps') as mock_gps, \
         patch('src.data.download.datarange') as mock_datarange, \
         patch('src.data.download.fetch_url') as mock_fetch:
        
        # Setup mocks
        mock_gps.return_value = mock_gwosc_data['gps_time']
        
        mock_ds = MagicMock()
        mock_ds.trange = (
            mock_gwosc_data['gps_time'] - 20,
            mock_gwosc_data['gps_time'] + 20
        )
        mock_datarange.return_value = [mock_ds]
        
        mock_fetch.return_value = {
            'L1': mock_gwosc_data['strain'],
            'H1': mock_gwosc_data['strain']
        }
        
        # Call the function
        results = fetch_batch_noise_segments(
            events=events,
            detectors=detectors,
            output_dir=temp_output_dir
        )
        
        # Verify results
        assert len(results) == 4  # 2 events * 2 detectors
        
        for event, detector, path in results:
            assert event in events
            assert detector in detectors
            assert path.exists()

def test_fetch_gw_noise_segment_handles_errors(temp_output_dir):
    """Test error handling when API fails."""
    with patch('src.data.download.event_gps') as mock_gps:
        mock_gps.side_effect = RuntimeError("API Error")
        
        with pytest.raises(RuntimeError):
            fetch_gw_noise_segment(
                event_name='GW150914',
                detector='L1',
                output_dir=temp_output_dir,
                retry_attempts=1
            )

def test_constants_are_defined():
    """Test that required constants are defined."""
    assert isinstance(DEFAULT_EVENTS, list)
    assert len(DEFAULT_EVENTS) > 0
    assert 'GW150914' in DEFAULT_EVENTS
    
    assert isinstance(DETECTORS, list)
    assert 'L1' in DETECTORS
    assert 'H1' in DETECTORS
    
    assert SEGMENT_DURATION > 0
    assert SAMPLE_RATE > 0