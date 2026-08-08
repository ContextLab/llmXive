import pytest
import pandas as pd
import os
from unittest.mock import patch, MagicMock
from src.ingestion import verify_schema, filter_antibiotic_use, filter_sleep_data, fetch_sample_headers, log_exclusion_rates
import json
import tempfile
from pathlib import Path

@pytest.fixture
def sample_df():
    """Create a sample dataframe for testing filtering logic."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'antibiotic_use_last_3m': [True, False, 'yes', 'no', None],
        'sleep_efficiency': [0.8, 0.7, None, 0.9, 0.6],
        'sleep_duration_hours': [7.0, 6.5, 8.0, None, 7.2],
        'other_col': [1, 2, 3, 4, 5]
    }
    return pd.DataFrame(data)

def test_antibiotic_exclusion_logic(sample_df):
    """
    Test T014: Verify samples with antibiotic_use_last_3m=True are filtered.
    Expected:
      S1: True -> EXCLUDE
      S2: False -> KEEP
      S3: 'yes' -> EXCLUDE
      S4: 'no' -> KEEP
      S5: None -> KEEP (treat as no antibiotic)
    Result should be S2, S4, S5 (3 rows).
    """
    filtered = filter_antibiotic_use(sample_df, 'antibiotic_use_last_3m')
    assert len(filtered) == 3
    assert 'S1' not in filtered['sample_id'].values
    assert 'S3' not in filtered['sample_id'].values
    assert 'S2' in filtered['sample_id'].values
    assert 'S4' in filtered['sample_id'].values
    assert 'S5' in filtered['sample_id'].values

def test_sleep_data_validation(sample_df):
    """
    Test T011: Verify samples with null sleep_efficiency or sleep_duration_hours are filtered.
    Input (after antibiotic filter S2, S4, S5):
      S2: eff=0.7, dur=6.5 -> KEEP
      S4: eff=0.9, dur=None -> EXCLUDE
      S5: eff=0.6, dur=7.2 -> KEEP
    Expected result: S2, S5 (2 rows).
    """
    # First filter antibiotic
    df_no_abx = filter_antibiotic_use(sample_df, 'antibiotic_use_last_3m')
    # Then filter sleep
    final = filter_sleep_data(df_no_abx, 'sleep_efficiency', 'sleep_duration_hours')
    
    assert len(final) == 2
    assert 'S2' in final['sample_id'].values
    assert 'S5' in final['sample_id'].values
    assert 'S4' not in final['sample_id'].values

def test_schema_verification_success():
    headers = ['sample_id', 'antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    required = ['sample_id', 'antibiotic_use_last_3m', 'sleep_efficiency']
    assert verify_schema(headers, required) is True

def test_schema_verification_missing_columns():
    headers = ['sample_id', 'antibiotic_use_last_3m']
    required = ['sample_id', 'antibiotic_use_last_3m', 'sleep_efficiency']
    assert verify_schema(headers, required) is False

def test_log_exclusion_rates():
    """Test that log_exclusion_rates creates the JSON file correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'report.json')
        result = log_exclusion_rates(100, 80, output_path)
        
        assert result['status'] == 'success'
        assert result['total_initial_sample_count'] == 100
        assert result['excluded_count'] == 20
        assert result['exclusion_proportion'] == 0.2
        assert result['remaining_count'] == 80
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == result