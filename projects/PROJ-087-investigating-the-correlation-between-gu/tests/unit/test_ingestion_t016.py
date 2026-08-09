import pytest
import pandas as pd
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions we're testing
from src.ingestion import (
    filter_antibiotic_use,
    filter_sleep_data,
    log_exclusion_rates,
    write_ingestion_report
)
from src.utils.hashing import compute_sha256

@pytest.fixture
def sample_df():
    """Create a sample dataframe for testing."""
    return pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'antibiotic_use_last_3m': [False, True, False, True, False],
        'sleep_efficiency': [0.85, 0.75, None, 0.90, 0.80],
        'sleep_duration_hours': [7.5, 6.0, 8.0, None, 7.0],
        'other_col': [1, 2, 3, 4, 5]
    })

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_filter_antibiotic_use(sample_df):
    """Test that antibiotic users are filtered out."""
    filtered = filter_antibiotic_use(sample_df)
    
    # Should exclude S2 and S4 (antibiotic_use_last_3m == True)
    assert len(filtered) == 3
    assert all(filtered['antibiotic_use_last_3m'] == False)
    assert 'S2' not in filtered['sample_id'].values
    assert 'S4' not in filtered['sample_id'].values

def test_filter_sleep_data(sample_df):
    """Test that samples with missing sleep data are filtered out."""
    filtered = filter_sleep_data(sample_df)
    
    # Should exclude S3 (missing sleep_efficiency) and S4 (missing sleep_duration_hours)
    assert len(filtered) == 3
    assert filtered['sleep_efficiency'].notna().all()
    assert filtered['sleep_duration_hours'].notna().all()
    assert 'S3' not in filtered['sample_id'].values
    assert 'S4' not in filtered['sample_id'].values

def test_combined_filtering(sample_df):
    """Test combined filtering of antibiotic use and missing sleep data."""
    # First filter antibiotic
    step1 = filter_antibiotic_use(sample_df)
    # Then filter sleep
    step2 = filter_sleep_data(step1)
    
    # Expected: S1, S5 (S2, S4 excluded for antibiotics; S3 excluded for missing sleep)
    assert len(step2) == 2
    assert set(step2['sample_id'].values) == {'S1', 'S5'}

def test_log_exclusion_rates_creates_file(temp_dir):
    """Test that log_exclusion_rates creates the report file."""
    output_path = temp_dir / "ingestion_report.json"
    initial_count = 100
    final_count = 80
    
    log_exclusion_rates(initial_count, final_count, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert report['total_initial_sample_count'] == initial_count
    assert report['excluded_count'] == 20
    assert report['exclusion_proportion'] == 0.2
    assert report['status'] == 'success'

def test_save_cleaned_dataset_and_checksum(temp_dir):
    """Test that cleaned dataset is saved and hash is recorded."""
    # Create sample data
    df = pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3'],
        'value': [1, 2, 3]
    })
    
    output_path = temp_dir / "cleaned_data.csv"
    checksums_path = temp_dir / "checksums.json"
    
    # Save dataframe
    df.to_csv(output_path, index=False)
    
    # Verify file exists
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    
    # Compute hash
    file_hash = compute_sha256(str(output_path))
    
    # Record hash
    checksums = {}
    if checksums_path.exists():
        with open(checksums_path, 'r') as f:
            checksums = json.load(f)
    checksums[output_path.name] = file_hash
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    # Verify hash file
    assert checksums_path.exists()
    with open(checksums_path, 'r') as f:
        saved_checksums = json.load(f)
    
    assert output_path.name in saved_checksums
    assert saved_checksums[output_path.name] == file_hash
    assert len(file_hash) == 64  # SHA-256 hex length