"""
Unit tests for the preprocessing module.
Tests T014 functionality: feature extraction and aggregation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocessing.preprocess import (
    load_source_data,
    extract_motion_features,
    aggregate_agency_scores,
    calculate_vif,
    run_preprocessing
)

@pytest.fixture
def sample_raw_data():
    """Fixture providing a DataFrame mimicking T013 synthetic output."""
    data = {
        'participant_id': ['P001', 'P002', 'P003', 'P004'],
        'latency': [150.5, 200.0, 120.0, 180.5],
        'smoothness': [0.85, 0.45, 0.92, 0.60],
        'lead_time': [50.0, -10.0, 25.0, 0.0],
        'agency_score': [4.2, 2.1, 4.8, 3.5],
        'extra_col': [1, 2, 3, 4]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_raw_data_missing():
    """Fixture with missing agency score."""
    data = {
        'participant_id': ['P001', 'P002'],
        'latency': [150.5, 200.0],
        'smoothness': [0.85, 0.45],
        'lead_time': [50.0, -10.0],
        'agency_score': [4.2, np.nan]
    }
    return pd.DataFrame(data)

def test_load_source_data_csv(tmp_path, sample_raw_data):
    """Test loading a CSV file."""
    file_path = tmp_path / "test_data.csv"
    sample_raw_data.to_csv(file_path, index=False)
    
    df = load_source_data(str(file_path))
    assert len(df) == 4
    assert 'latency' in df.columns

def test_extract_motion_features_passthrough(sample_raw_data):
    """Test that extract_motion_features passes through existing columns."""
    df = extract_motion_features(sample_raw_data)
    assert 'latency' in df.columns
    assert 'smoothness' in df.columns
    assert 'lead_time' in df.columns
    # Check values are preserved
    assert df['latency'].iloc[0] == 150.5

def test_aggregate_agency_scores(sample_raw_data):
    """Test agency score aggregation."""
    df = aggregate_agency_scores(sample_raw_data)
    assert 'agency_score' in df.columns
    assert len(df) == 4

def test_aggregate_agency_scores_drops_nan(sample_raw_data_missing):
    """Test that rows with missing agency score are dropped."""
    df = aggregate_agency_scores(sample_raw_data_missing)
    assert len(df) == 1
    assert not df['agency_score'].isna().any()

def test_calculate_vif(sample_raw_data):
    """Test VIF calculation."""
    features = ['latency', 'smoothness', 'lead_time']
    vif_df = calculate_vif(sample_raw_data, features)
    
    assert 'feature' in vif_df.columns
    assert 'vif' in vif_df.columns
    assert len(vif_df) == 3
    # VIF should be >= 1
    assert all(vif_df['vif'] >= 1.0)

def test_run_preprocessing_integration(tmp_path, sample_raw_data):
    """Test the full preprocessing pipeline."""
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.csv"
    
    sample_raw_data.to_csv(input_path, index=False)
    
    stats = run_preprocessing(str(input_path), str(output_path))
    
    assert Path(output_path).exists()
    assert stats['rows_processed'] == 4
    assert 'latency' in stats['columns']
    assert 'agency_score' in stats['columns']
    
    # Verify output content
    out_df = pd.read_csv(output_path)
    assert len(out_df) == 4