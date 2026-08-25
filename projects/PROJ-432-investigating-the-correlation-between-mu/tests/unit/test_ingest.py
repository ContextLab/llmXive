import pytest
from pathlib import Path
import sys
import os
import tempfile
import shutil
import pandas as pd
from datetime import datetime
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data.ingest import (
    log_exclusion_event,
    align_temporal_data,
    validate_icecube_data,
    validate_era5_data
)
from src.data.utils import write_json_log

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)

def test_log_exclusion_event_creates_file(temp_data_dir):
    """Test that log_exclusion_event creates the exclusion log file."""
    log_path = Path(temp_data_dir) / "alignment.json"
    
    # Mock the global EXCLUSION_LOG_PATH for this test
    import src.data.ingest as ingest_module
    original_path = ingest_module.EXCLUSION_LOG_PATH
    ingest_module.EXCLUSION_LOG_PATH = log_path
    
    try:
        log_exclusion_event("2023-01-01", "missing_era5", "era5")
        assert log_path.exists()
        
        with open(log_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["date"] == "2023-01-01"
        assert data[0]["reason"] == "missing_era5"
    finally:
        ingest_module.EXCLUSION_LOG_PATH = original_path

def test_log_exclusion_event_appends_to_existing(temp_data_dir):
    """Test that log_exclusion_event appends to existing log."""
    log_path = Path(temp_data_dir) / "alignment.json"
    
    # Create initial log
    initial_data = [{"date": "2023-01-01", "reason": "test", "source": "test"}]
    with open(log_path, 'w') as f:
        json.dump(initial_data, f)
    
    import src.data.ingest as ingest_module
    original_path = ingest_module.EXCLUSION_LOG_PATH
    ingest_module.EXCLUSION_LOG_PATH = log_path
    
    try:
        log_exclusion_event("2023-01-02", "missing_icecube", "icecube")
        
        with open(log_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 2
        assert data[1]["date"] == "2023-01-02"
    finally:
        ingest_module.EXCLUSION_LOG_PATH = original_path

def test_align_temporal_data_logs_missing_dates(temp_data_dir):
    """Test that align_temporal_data logs missing dates."""
    # Create mock data with specific date gaps
    icecube_data = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01', '2023-01-03']),
        'count': [100, 120]
    })
    
    era5_data = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-02', '2023-01-03']),
        'pressure_level': [500, 500],
        'temperature': [250, 255],
        'geopotential': [5000, 5100]
    })
    
    log_path = Path(temp_data_dir) / "alignment.json"
    
    import src.data.ingest as ingest_module
    original_path = ingest_module.EXCLUSION_LOG_PATH
    ingest_module.EXCLUSION_LOG_PATH = log_path
    
    try:
        aligned = align_temporal_data(icecube_data, era5_data)
        
        # Should only have 2023-01-03 (intersection)
        assert len(aligned) == 1
        assert aligned['date'].iloc[0] == pd.Timestamp('2023-01-03')
        
        # Check log for missing dates
        with open(log_path, 'r') as f:
            logs = json.load(f)
        
        # Should have logs for 2023-01-01 (missing era5) and 2023-01-02 (missing icecube)
        dates_logged = [log['date'] for log in logs]
        assert '2023-01-01' in dates_logged
        assert '2023-01-02' in dates_logged
        
        # Verify reasons
        reason_map = {log['date']: log['reason'] for log in logs}
        assert reason_map['2023-01-01'] == 'missing_era5'
        assert reason_map['2023-01-02'] == 'missing_icecube'
    finally:
        ingest_module.EXCLUSION_LOG_PATH = original_path

def test_align_temporal_data_no_gaps():
    """Test alignment when both datasets have identical dates."""
    icecube_data = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01', '2023-01-02']),
        'count': [100, 120]
    })
    
    era5_data = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01', '2023-01-02']),
        'pressure_level': [500, 500],
        'temperature': [250, 255],
        'geopotential': [5000, 5100]
    })
    
    aligned = align_temporal_data(icecube_data, era5_data)
    
    assert len(aligned) == 2
    assert list(aligned['date']) == [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-02')]

def test_align_temporal_data_empty_intersection():
    """Test alignment when datasets have no common dates."""
    icecube_data = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01', '2023-01-02']),
        'count': [100, 120]
    })
    
    era5_data = pd.DataFrame({
        'date': pd.to_datetime(['2023-02-01', '2023-02-02']),
        'pressure_level': [500, 500],
        'temperature': [250, 255],
        'geopotential': [5000, 5100]
    })
    
    log_path = tempfile.mktemp(suffix='.json')
    
    import src.data.ingest as ingest_module
    original_path = ingest_module.EXCLUSION_LOG_PATH
    ingest_module.EXCLUSION_LOG_PATH = Path(log_path)
    
    try:
        aligned = align_temporal_data(icecube_data, era5_data)
        
        # Result should be empty
        assert len(aligned) == 0
        
        # All dates should be logged as missing from the other source
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                logs = json.load(f)
            # We expect 2 logs for icecube missing era5 and 2 for era5 missing icecube
            assert len(logs) == 4
    finally:
        ingest_module.EXCLUSION_LOG_PATH = original_path
        if os.path.exists(log_path):
            os.remove(log_path)

def test_validate_icecube_data_valid():
    """Test validation of valid IceCube data."""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01']),
        'count': [100]
    })
    assert validate_icecube_data(df) is True

def test_validate_icecube_data_invalid_negative():
    """Test validation of IceCube data with negative counts."""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01']),
        'count': [-100]
    })
    assert validate_icecube_data(df) is False

def test_validate_icecube_data_missing_columns():
    """Test validation of IceCube data with missing columns."""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01']),
        'count': [100]
    })
    # Remove count column
    df = df.drop(columns=['count'])
    assert validate_icecube_data(df) is False

def test_validate_era5_data_valid():
    """Test validation of valid ERA5 data."""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01']),
        'pressure_level': [500],
        'temperature': [250]
    })
    assert validate_era5_data(df) is True

def test_validate_era5_data_missing_columns():
    """Test validation of ERA5 data with missing columns."""
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01']),
        'pressure_level': [500]
    })
    assert validate_era5_data(df) is False

def test_validate_era5_data_out_of_range_pressure():
    """Test validation of ERA5 data with pressure outside expected range."""
    # Pressure should be between 10 and 1000 hPa
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01']),
        'pressure_level': [1001], # Out of range
        'temperature': [250]
    })
    assert validate_era5_data(df) is False

def test_validate_era5_data_negative_temperature():
    """Test validation of ERA5 data with physically impossible temperature."""
    # Kelvin temperature should be positive
    df = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01']),
        'pressure_level': [500],
        'temperature': [-50] # Negative Kelvin is impossible
    })
    assert validate_era5_data(df) is False