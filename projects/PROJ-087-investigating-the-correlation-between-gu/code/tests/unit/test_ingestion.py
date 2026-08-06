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
    return pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3', 'S4'],
        'antibiotic_use_last_3m': [False, True, None, False],
        'sleep_efficiency': [0.85, 0.70, None, 0.90],
        'sleep_duration_hours': [7.0, 6.5, 8.0, None]
    })

def test_antibiotic_exclusion_logic(sample_df):
    """Test that samples with antibiotic_use_last_3m=True are filtered."""
    result = filter_antibiotic_use(sample_df)
    # S2 has True, should be excluded
    assert len(result) == 3
    assert 'S2' not in result['sample_id'].values

def test_sleep_data_validation(sample_df):
    """Test that samples with null sleep_efficiency or sleep_duration_hours are filtered."""
    # First apply antibiotic filter to get a clean baseline
    df_no_abx = filter_antibiotic_use(sample_df)
    result = filter_sleep_data(df_no_abx)
    # S3 has null sleep_efficiency, S4 has null sleep_duration_hours
    # S1 is the only one with both valid
    assert len(result) == 1
    assert 'S1' in result['sample_id'].values

def test_schema_verification_success():
    headers = ['sample_id', 'antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    required = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    assert verify_schema(headers, required) is True

def test_schema_verification_missing_columns():
    headers = ['sample_id', 'antibiotic_use_last_3m']
    required = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    assert verify_schema(headers, required) is False

def test_log_exclusion_rates():
    """Test that log_exclusion_rates creates the correct JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'test_report.json')
        total_initial = 100
        excluded_count = 25
        
        log_exclusion_rates(total_initial, excluded_count, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert report['total_initial_sample_count'] == 100
        assert report['excluded_count'] == 25
        assert report['exclusion_proportion'] == 0.25
        assert report['retained_count'] == 75