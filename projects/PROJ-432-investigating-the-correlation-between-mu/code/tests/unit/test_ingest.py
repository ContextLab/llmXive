import pytest
from pathlib import Path
import sys
import os
import tempfile
import shutil
import json
import pandas as pd

# Add the project root to the path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.data.ingest import log_exclusion_event, align_temporal_data, REASON_MISSING_ERA5, REASON_ICECUBE_MAINTENANCE, SOURCE_ERA5, SOURCE_ICECUBE

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_log_exclusion_event_creates_file(temp_data_dir):
    """Test that log_exclusion_event creates the log file if it doesn't exist."""
    log_path = temp_data_dir / "logs" / "alignment.json"
    log_exclusion_event(log_path, "2023-01-01", REASON_MISSING_ERA5, SOURCE_ERA5)
    
    assert log_path.exists()
    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["date"] == "2023-01-01"
    assert data[0]["reason"] == REASON_MISSING_ERA5
    assert data[0]["source"] == SOURCE_ERA5

def test_log_exclusion_event_appends_to_existing(temp_data_dir):
    """Test that log_exclusion_event appends to an existing log file."""
    log_path = temp_data_dir / "logs" / "alignment.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create initial log
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump([{"date": "2023-01-01", "reason": "other", "source": "icecube"}], f)
    
    log_exclusion_event(log_path, "2023-01-02", REASON_MISSING_ERA5, SOURCE_ERA5)
    
    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert len(data) == 2
    assert data[1]["date"] == "2023-01-02"

def test_align_temporal_data_logs_missing_dates(temp_data_dir):
    """Test that align_temporal_data logs exclusion events for missing dates."""
    log_path = temp_data_dir / "logs" / "alignment.json"
    
    # Create mock data
    df_icecube = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03']),
        'muon_count': [100, 200, 300]
    })
    df_era5 = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-02', '2023-01-03', '2023-01-04']),
        'temperature': [20.0, 21.0, 22.0],
        'pressure': [1000.0, 1001.0, 1002.0]
    })
    
    aligned = align_temporal_data(df_icecube, df_era5, log_path)
    
    # Check that alignment worked for common dates
    assert len(aligned) == 2
    assert set(aligned['date'].dt.date) == {pd.Timestamp('2023-01-02').date(), pd.Timestamp('2023-01-03').date()}
    
    # Check that exclusion events were logged
    assert log_path.exists()
    with open(log_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert len(data) == 2
    # One missing from era5 (2023-01-01) and one missing from icecube (2023-01-04)
    reasons = {entry["reason"] for entry in data}
    assert REASON_MISSING_ERA5 in reasons
    assert REASON_ICECUBE_MAINTENANCE in reasons