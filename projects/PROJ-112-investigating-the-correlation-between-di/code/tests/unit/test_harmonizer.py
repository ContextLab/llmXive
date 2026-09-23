"""
Unit tests for the harmonizer module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from src.ingestion.harmonizer import (
    load_agp_data,
    load_ukbb_data,
    harmonize_fiber_units,
    filter_samples,
    merge_datasets,
    harmonize_and_merge,
    write_exclusion_log
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_agp_df():
    """Create a sample AGP DataFrame."""
    data = {
        'sample_id': ['AGP_001', 'AGP_002', 'AGP_003', 'AGP_004', 'AGP_005'],
        'fiber_g_day': [25.5, 15.0, np.nan, 250.0, 4.0],  # One missing, one out of range
        'read_count': [10000, 3000, 8000, 6000, 2000]  # Two below threshold
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_ukbb_df():
    """Create a sample UKBB DataFrame."""
    data = {
        'sample_id': ['UKBB_001', 'UKBB_002', 'UKBB_003', 'UKBB_004'],
        'fiber_g_day': [30.0, 18.5, -5.0, 100.0],  # One out of range (negative)
        'read_count': [12000, 4500, 9000, 7000]  # One below threshold
    }
    return pd.DataFrame(data)

def test_filter_samples_agp(sample_agp_df, temp_dir):
    """Test filtering logic on AGP data."""
    exclusion_log = []
    
    filtered = filter_samples(sample_agp_df.copy(), "AGP", exclusion_log)
    
    # Expected exclusions:
    # - AGP_003: missing fiber
    # - AGP_004: fiber > 200
    # - AGP_002: read_count < 5000
    # - AGP_005: read_count < 5000
    # Remaining: AGP_001 (valid)
    
    assert len(filtered) == 1
    assert filtered['sample_id'].iloc[0] == 'AGP_001'
    assert filtered['fiber_g_day'].iloc[0] == 25.5
    assert filtered['read_count'].iloc[0] == 10000
    
    # Check exclusion log
    assert len(exclusion_log) == 3  # 3 different exclusion reasons
    
    reasons = [r['reason'] for r in exclusion_log]
    assert 'missing_fiber_data' in reasons
    assert 'read_count_below_5000' in reasons
    assert 'fiber_outside_0.0_200.0g_day' in reasons

def test_filter_samples_ukbb(sample_ukbb_df, temp_dir):
    """Test filtering logic on UKBB data."""
    exclusion_log = []
    
    filtered = filter_samples(sample_ukbb_df.copy(), "UKBB", exclusion_log)
    
    # Expected exclusions:
    # - UKBB_002: read_count < 5000
    # - UKBB_003: fiber < 0
    # Remaining: UKBB_001, UKBB_004
    
    assert len(filtered) == 2
    assert set(filtered['sample_id'].tolist()) == {'UKBB_001', 'UKBB_004'}

def test_harmonize_fiber_units():
    """Test fiber unit harmonization."""
    df = pd.DataFrame({
        'sample_id': ['S1', 'S2'],
        'fiber_g_day': [20.5, 30.0],
        'read_count': [5000, 6000]
    })
    
    harmonized = harmonize_fiber_units(df, "TEST")
    
    assert list(harmonized.columns) == list(df.columns)
    assert harmonized['fiber_g_day'].dtype in [np.float64, np.float32]

def test_merge_datasets(sample_agp_df, sample_ukbb_df):
    """Test merging of AGP and UKBB datasets."""
    # First filter both
    agp_log = []
    ukbb_log = []
    
    filtered_agp = filter_samples(sample_agp_df.copy(), "AGP", agp_log)
    filtered_ukbb = filter_samples(sample_ukbb_df.copy(), "UKBB", ukbb_log)
    
    merged = merge_datasets(filtered_agp, filtered_ukbb)
    
    # Check cohort_id column exists and has correct values
    assert 'cohort_id' in merged.columns
    assert 'AGP' in merged['cohort_id'].values
    assert 'UKBB' in merged['cohort_id'].values
    
    # Check sample counts
    assert len(merged) == len(filtered_agp) + len(filtered_ukbb)
    
    # Check column order
    assert merged.columns[0] == 'sample_id'
    assert merged.columns[1] == 'cohort_id'
    assert merged.columns[2] == 'fiber_g_day'
    assert merged.columns[3] == 'read_count'

def test_harmonize_and_merge_integration(temp_dir):
    """Test full harmonization and merge pipeline."""
    # Create sample data files
    agp_path = temp_dir / "agp_raw.tsv"
    ukbb_path = temp_dir / "ukbb_raw.tsv"
    output_path = temp_dir / "merged_harmonized.tsv"
    log_path = temp_dir / "harmonization_log.txt"
    
    # Sample data
    agp_data = {
        'sample_id': ['AGP_001', 'AGP_002', 'AGP_003'],
        'fiber_g_day': [25.0, 30.0, 15.0],
        'read_count': [10000, 8000, 6000]
    }
    
    ukbb_data = {
        'sample_id': ['UKBB_001', 'UKBB_002', 'UKBB_003'],
        'fiber_g_day': [20.0, 22.0, 18.0],
        'read_count': [9000, 7000, 11000]
    }
    
    pd.DataFrame(agp_data).to_csv(agp_path, sep='\t', index=False)
    pd.DataFrame(ukbb_data).to_csv(ukbb_path, sep='\t', index=False)
    
    # Run harmonization
    result_df = harmonize_and_merge(
        agp_path=agp_path,
        ukbb_path=ukbb_path,
        output_path=output_path,
        log_path=log_path
    )
    
    # Verify output file exists
    assert output_path.exists()
    assert log_path.exists()
    
    # Verify result
    assert len(result_df) == 6  # All samples should pass filters
    assert 'cohort_id' in result_df.columns
    assert set(result_df['cohort_id'].unique()) == {'AGP', 'UKBB'}
    
    # Verify output file content
    loaded_output = pd.read_csv(output_path, sep='\t')
    assert len(loaded_output) == 6
    assert 'cohort_id' in loaded_output.columns