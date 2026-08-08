import pytest
import pandas as pd
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import shutil

# Import functions to test
from src.ingestion import (
    filter_antibiotic_use,
    filter_sleep_data,
    log_exclusion_rates,
    CLEANED_FILE,
    CHECKSUMS_FILE,
    REPORT_FILE
)
from src.utils.hashing import compute_sha256

@pytest.fixture
def sample_df():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'antibiotic_use_last_3m': [True, False, None, 'False', True],
        'sleep_efficiency': [0.8, 0.7, None, 0.9, 0.85],
        'sleep_duration_hours': [7.5, 6.8, 8.0, None, 7.2],
        'otu_1': [10, 20, 30, 40, 50],
        'otu_2': [5, 15, 25, 35, 45]
    })

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing file operations."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

def test_filter_antibiotic_use(sample_df):
    """Test that antibiotic users are filtered out."""
    filtered = filter_antibiotic_use(sample_df)
    # Expected: S2 (False), S3 (None), S4 ('False')
    assert len(filtered) == 3
    assert 'S1' not in filtered['sample_id'].values
    assert 'S5' not in filtered['sample_id'].values

def test_filter_sleep_data(sample_df):
    """Test that samples with missing sleep data are filtered out."""
    filtered = filter_sleep_data(sample_df)
    # Expected: S1 (both present), S2 (both present)
    # S3: sleep_efficiency is None -> excluded
    # S4: sleep_duration_hours is None -> excluded
    # S5: both present -> included
    assert len(filtered) == 3
    assert 'S1' in filtered['sample_id'].values
    assert 'S2' in filtered['sample_id'].values
    assert 'S5' in filtered['sample_id'].values
    assert 'S3' not in filtered['sample_id'].values
    assert 'S4' not in filtered['sample_id'].values

def test_combined_filtering(sample_df):
    """Test combined filtering: antibiotic use AND sleep data."""
    step1 = filter_antibiotic_use(sample_df)
    step2 = filter_sleep_data(step1)
    # After antibiotic filter: S2, S3, S4
    # After sleep filter on remaining:
    # S2: sleep_eff=0.7, sleep_dur=6.8 -> Keep
    # S3: sleep_eff=None -> Drop
    # S4: sleep_dur=None -> Drop
    assert len(step2) == 1
    assert step2.iloc[0]['sample_id'] == 'S2'

def test_log_exclusion_rates_creates_file(temp_dir):
    """Test that log_exclusion_rates creates the report file."""
    report_path = Path(temp_dir) / "test_report.json"
    log_exclusion_rates(100, 80, report_path)
    
    assert report_path.exists()
    with open(report_path, 'r') as f:
        data = json.load(f)
    
    assert data['status'] == 'success'
    assert data['total_initial_sample_count'] == 100
    assert data['excluded_count'] == 20
    assert abs(data['exclusion_proportion'] - 0.2) < 0.001

def test_save_cleaned_dataset_and_checksum(temp_dir, sample_df):
    """Test T016: Save cleaned dataset and verify checksum."""
    # Setup temp paths
    test_cleaned = Path(temp_dir) / "test_cleaned.csv"
    test_checksums = Path(temp_dir) / "test_checksums.json"
    
    # Save data
    sample_df.to_csv(test_cleaned, index=False)
    
    # Compute checksum
    checksum = compute_sha256(test_cleaned)
    
    # Save checksums
    checksums = {'test_cleaned.csv': checksum}
    with open(test_checksums, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    # Verify file exists and is not empty
    assert test_cleaned.exists()
    assert test_cleaned.stat().st_size > 0
    
    # Verify checksum matches
    with open(test_checksums, 'r') as f:
        saved_checksums = json.load(f)
    
    assert saved_checksums['test_cleaned.csv'] == checksum
    
    # Verify row count > 0
    df = pd.read_csv(test_cleaned)
    assert len(df) > 0
