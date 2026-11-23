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
    write_exclusion_log,
    harmonize_and_merge
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def sample_agp_df():
    data = {
        'sample_id': ['AGP_001', 'AGP_002', 'AGP_003', 'AGP_004'],
        'fiber_g_day': [25.0, 150.0, -5.0, np.nan],
        'read_count': [6000, 4000, 10000, 8000],
        'taxon_A': [0.1, 0.2, 0.3, 0.4]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_ukbb_df():
    data = {
        'sample_id': ['UKBB_001', 'UKBB_002', 'UKBB_003'],
        'fiber_g_day': [30.0, 250.0, 50.0],
        'read_count': [7000, 6000, 2000],
        'taxon_B': [0.5, 0.6, 0.7]
    }
    return pd.DataFrame(data)

@pytest.fixture
def agp_input_file(temp_dir, sample_agp_df):
    path = temp_dir / "agp_raw.tsv"
    sample_agp_df.to_csv(path, sep='\t', index=False)
    return path

@pytest.fixture
def ukbb_input_file(temp_dir, sample_ukbb_df):
    path = temp_dir / "ukbb_raw.tsv"
    sample_ukbb_df.to_csv(path, sep='\t', index=False)
    return path

def test_load_agp_data(agp_input_file, sample_agp_df):
    df = load_agp_data(agp_input_file)
    assert len(df) == len(sample_agp_df)
    assert 'fiber_g_day' in df.columns
    assert 'read_count' in df.columns

def test_load_ukbb_data(ukbb_input_file, sample_ukbb_df):
    df = load_ukbb_data(ukbb_input_file)
    assert len(df) == len(sample_ukbb_df)

def test_harmonize_fiber_units(sample_agp_df):
    df = harmonize_fiber_units(sample_agp_df, "AGP")
    assert df['fiber_g_day'].dtype in [np.float64, np.float32]

def test_filter_samples_agp(sample_agp_df):
    # AGP_001: pass (25g, 6000 reads)
    # AGP_002: fail (4000 reads)
    # AGP_003: fail (-5g)
    # AGP_004: fail (NaN)
    df, stats = filter_samples(sample_agp_df, "AGP")
    assert len(df) == 1
    assert df.iloc[0]['sample_id'] == 'AGP_001'
    assert stats['excluded_missing_fiber'] == 1
    assert stats['excluded_read_count'] == 1
    assert stats['excluded_fiber_range'] == 1
    assert stats['final_count'] == 1

def test_filter_samples_ukbb(sample_ukbb_df):
    # UKBB_001: pass (30g, 7000 reads)
    # UKBB_002: fail (250g > 200)
    # UKBB_003: fail (2000 reads)
    df, stats = filter_samples(sample_ukbb_df, "UKBB")
    assert len(df) == 1
    assert df.iloc[0]['sample_id'] == 'UKBB_001'
    assert stats['excluded_fiber_range'] == 1
    assert stats['excluded_read_count'] == 1

def test_merge_datasets(sample_agp_df, sample_ukbb_df):
    # Filter first to ensure valid inputs for merge
    agp_filtered, _ = filter_samples(sample_agp_df, "AGP")
    ukbb_filtered, _ = filter_samples(sample_ukbb_df, "UKBB")
    
    merged = merge_datasets(agp_filtered, ukbb_filtered)
    
    assert len(merged) == 2
    assert 'cohort_id' in merged.columns
    assert set(merged['cohort_id'].unique()) == {'AGP', 'UKBB'}
    assert 'sample_id' in merged.columns
    assert 'fiber_g_day' in merged.columns
    assert 'read_count' in merged.columns

def test_write_exclusion_log(temp_dir):
    stats = [
        {
            'source': 'TEST',
            'initial_count': 10,
            'excluded_missing_fiber': 1,
            'excluded_read_count': 2,
            'excluded_fiber_range': 3,
            'final_count': 4
        }
    ]
    log_path = temp_dir / "test_log.txt"
    write_exclusion_log(stats, log_path)
    
    assert log_path.exists()
    content = log_path.read_text()
    assert "TEST" in content
    assert "Initial: 10" in content

def test_harmonize_and_merge_integration(temp_dir, agp_input_file, ukbb_input_file):
    output_path = temp_dir / "merged.tsv"
    log_path = temp_dir / "log.txt"
    
    df = harmonize_and_merge(
        agp_path=agp_input_file,
        ukbb_path=ukbb_input_file,
        output_path=output_path,
        exclusion_log_path=log_path
    )
    
    assert df is not None
    assert output_path.exists()
    assert log_path.exists()
    assert 'cohort_id' in df.columns
    assert len(df) == 2 # 1 from AGP, 1 from UKBB based on fixture data