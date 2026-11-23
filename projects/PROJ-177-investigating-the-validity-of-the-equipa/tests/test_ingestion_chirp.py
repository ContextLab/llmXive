"""
Tests for T063: verify_chirp_segments function.
"""
import json
import os
import tempfile
import warnings
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ingestion import verify_chirp_segments, DataExclusionWarning

@pytest.fixture
def sample_data():
    """Create sample data with timestamps."""
    n = 200
    timestamps = np.linspace(0, 10, n)
    df = pd.DataFrame({
        'timestamp': timestamps,
        'x': np.random.randn(n),
        'y': np.random.randn(n),
        'z': np.random.randn(n),
        'particle_id': [1] * n
    })
    return df

@pytest.fixture
def chirp_mask_file(tmp_path):
    """Create a chirp mask CSV file."""
    n = 200
    timestamps = np.linspace(0, 10, n)
    # Create a mask where 25% of frames are excluded in the middle
    chirp_flags = [False] * 50 + [True] * 100 + [False] * 50
    
    df = pd.DataFrame({
        'timestamp': timestamps,
        'chirp_flag': chirp_flags
    })
    
    file_path = tmp_path / "chirp_mask.csv"
    df.to_csv(file_path, index=False)
    return str(file_path)

@pytest.fixture
def empty_chirp_mask_file(tmp_path):
    """Create a chirp mask with no exclusions."""
    n = 200
    timestamps = np.linspace(0, 10, n)
    df = pd.DataFrame({
        'timestamp': timestamps,
        'chirp_flag': [False] * n
    })
    
    file_path = tmp_path / "chirp_mask.csv"
    df.to_csv(file_path, index=False)
    return str(file_path)

def test_verify_chirp_segments_counts_exclusions(sample_data, chirp_mask_file):
    """Test that verify_chirp_segments correctly counts excluded frames."""
    result = verify_chirp_segments(sample_data, chirp_mask_file, window_size=50)
    
    assert result['total_frames'] == 200
    assert result['excluded_frames'] == 100
    assert abs(result['excluded_percentage'] - 50.0) < 0.1

def test_verify_chirp_segments_detects_windows(sample_data, chirp_mask_file):
    """Test that windows exceeding 20% threshold are detected."""
    result = verify_chirp_segments(sample_data, chirp_mask_file, window_size=50)
    
    assert len(result['windows_exceeding_threshold']) > 0
    for window in result['windows_exceeding_threshold']:
        assert window['excluded_percentage'] > 20.0

def test_verify_chirp_segments_raises_warning(sample_data, chirp_mask_file):
    """Test that DataExclusionWarning is raised when threshold exceeded."""
    with pytest.warns(DataExclusionWarning):
        verify_chirp_segments(sample_data, chirp_mask_file, window_size=50)

def test_verify_chirp_segments_no_exclusions(sample_data, empty_chirp_mask_file):
    """Test behavior when no frames are excluded."""
    result = verify_chirp_segments(sample_data, empty_chirp_mask_file, window_size=50)
    
    assert result['excluded_frames'] == 0
    assert result['excluded_percentage'] == 0.0
    assert len(result['windows_exceeding_threshold']) == 0

def test_verify_chirp_segments_missing_file(sample_data, tmp_path):
    """Test behavior when chirp mask file is missing."""
    missing_path = tmp_path / "nonexistent.csv"
    result = verify_chirp_segments(sample_data, str(missing_path), window_size=50)
    
    assert result['excluded_frames'] == 0
    assert result['excluded_percentage'] == 0.0

def test_verify_chirp_segments_creates_report(sample_data, chirp_mask_file, tmp_path, monkeypatch):
    """Test that exclusion report is created when thresholds exceeded."""
    # Change cwd to tmp_path for artifact writing
    monkeypatch.chdir(tmp_path)
    
    # Ensure artifacts directory exists
    (tmp_path / "artifacts").mkdir(exist_ok=True)
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = verify_chirp_segments(sample_data, chirp_mask_file, window_size=50)
        
        assert len(w) == 1
        assert issubclass(w[0].category, DataExclusionWarning)
    
    report_path = tmp_path / "artifacts" / "exclusion_report.json"
    assert report_path.exists()
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert 'total_frames' in report
    assert 'excluded_frames' in report
    assert 'windows_exceeding_threshold' in report
    assert len(report['windows_exceeding_threshold']) > 0
