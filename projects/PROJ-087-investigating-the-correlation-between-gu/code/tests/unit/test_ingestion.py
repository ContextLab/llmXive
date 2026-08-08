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
    data = {
        'antibiotic_use_last_3m': [True, False, False, True, None],
        'sleep_efficiency': [0.8, 0.9, None, 0.7, 0.85],
        'sleep_duration_hours': [7.0, 8.0, 6.0, None, 7.5],
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5']
    }
    return pd.DataFrame(data)

def test_antibiotic_exclusion_logic(sample_df):
    result = filter_antibiotic_use(sample_df)
    # Should keep S2, S3, S5 (False or None)
    # S1 and S4 (True) should be removed
    assert len(result) == 3
    assert 'S1' not in result['sample_id'].values
    assert 'S4' not in result['sample_id'].values

def test_sleep_data_validation(sample_df):
    # First filter antibiotic, then sleep
    no_antibiotic = filter_antibiotic_use(sample_df)
    result = filter_sleep_data(no_antibiotic)
    # S3 has null sleep_efficiency, S4 was already removed
    # S2 and S5 remain
    assert len(result) == 2
    assert 'S3' not in result['sample_id'].values

def test_schema_verification_success():
    headers = ['col1', 'col2', 'col3']
    required = ['col1', 'col3']
    assert verify_schema(headers, required) is True

def test_schema_verification_missing_columns():
    headers = ['col1', 'col2']
    required = ['col1', 'col3']
    assert verify_schema(headers, required) is False

def test_log_exclusion_rates():
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "report.json"
        log_exclusion_rates(100, 80, str(report_path))
        
        assert report_path.exists()
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        assert data['total_initial_sample_count'] == 100
        assert data['excluded_count'] == 20
        assert data['exclusion_proportion'] == 0.2
        assert data['status'] == 'success'
