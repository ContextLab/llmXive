import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os
from code.utils import safe_write_csv, setup_logging
from code.entropy import process_single_parcels, run_parcels_processing

# Mock functions for testing if real ones are not available
def mock_compute_multiscale_entropy(ts, m=2, r_factor=0.2, scale_range=(1, 20)):
    """Mock function to return a dummy entropy value."""
    return np.random.rand() * 10.0

# Patch the function if it doesn't exist in the real module
try:
    from code.entropy import compute_multiscale_entropy
except ImportError:
    # If not available, use mock
    pass

@pytest.fixture
def mock_time_series():
    """Generate a mock time series with no NaNs."""
    return np.random.rand(100, 10)  # 100 timepoints, 10 parcels

@pytest.fixture
def mock_parcel_map():
    """Generate a mock parcel map."""
    return {i: f'NET_{i}' for i in range(1, 11)}

def test_process_single_parcels_no_nan(mock_time_series, mock_parcel_map):
    """Test process_single_parcels with no NaNs."""
    results = process_single_parcels(
        subject_id="SUB001",
        time_series=mock_time_series,
        parcel_map=mock_parcel_map,
        scale_range=(1, 5),
        m=2,
        r_factor=0.2
    )
    
    assert len(results) == 10  # All 10 parcels should be processed
    assert all(r['valid'] for r in results)
    assert all('entropy_auc' in r for r in results)

def test_process_single_parcels_with_nan(mock_parcel_map):
    """Test process_single_parcels with NaNs in time series."""
    ts = np.random.rand(100, 10)
    ts[10, 5] = np.nan  # Introduce NaN in parcel 6 (index 5)
    
    results = process_single_parcels(
        subject_id="SUB002",
        time_series=ts,
        parcel_map=mock_parcel_map,
        scale_range=(1, 5),
        m=2,
        r_factor=0.2
    )
    
    # One parcel should be skipped
    assert len(results) == 9
    # Check that parcel 6 is not in results
    parcel_ids = [r['parcel_id'] for r in results]
    assert 6 not in parcel_ids

def test_run_parcels_processing(tmp_path):
    """Test the main orchestration function."""
    # Create mock valid subjects file
    valid_subjects = pd.DataFrame({'subject_id': ['SUB001', 'SUB002']})
    valid_path = tmp_path / "valid_subjects.csv"
    safe_write_csv(valid_subjects, str(valid_path))
    
    # Create mock time series files
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    
    for sub_id in ['SUB001', 'SUB002']:
        ts = np.random.rand(100, 10)
        np.save(raw_dir / f"{sub_id}_scrubbed_ts.npy", ts)
    
    output_path = tmp_path / "entropy_parcels.csv"
    
    # Run the function
    run_parcels_processing(
        valid_subjects_path=str(valid_path),
        raw_data_dir=str(raw_dir),
        output_path=str(output_path),
        atlas_path=None
    )
    
    # Check output file exists and has content
    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert len(df) > 0
    assert 'subject_id' in df.columns
    assert 'entropy_auc' in df.columns