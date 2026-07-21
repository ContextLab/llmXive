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
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'antibiotic_use_last_3m': [False, True, False, 'true', 'yes'],
        'sleep_efficiency': [0.85, 0.75, None, 0.90, 0.80],
        'sleep_duration_hours': [7.5, 6.5, 8.0, None, 7.0]
    })

def test_antibiotic_exclusion_logic(sample_df):
    """Test that antibiotic users are correctly excluded."""
    result = filter_antibiotic_use(sample_df)
    
    # Should exclude S2 (True), S4 ('true'), S5 ('yes')
    expected_ids = ['S1', 'S3']
    assert list(result['sample_id']) == expected_ids
    assert len(result) == 2

def test_sleep_data_validation(sample_df):
    """Test that samples with missing sleep data are excluded."""
    # First apply antibiotic filter to get clean data
    df_no_antibiotic = filter_antibiotic_use(sample_df)
    
    result = filter_sleep_data(df_no_antibiotic)
    
    # Should exclude S3 (None sleep_efficiency)
    expected_ids = ['S1']
    assert list(result['sample_id']) == expected_ids
    assert len(result) == 1

def test_schema_verification_success():
    """Test schema verification with all required columns present."""
    headers = ['sample_id', 'antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    required = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    
    assert verify_schema(headers, required) is True

def test_schema_verification_missing_columns():
    """Test schema verification with missing columns."""
    headers = ['sample_id', 'antibiotic_use_last_3m']
    required = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    
    assert verify_schema(headers, required) is False

def test_log_exclusion_rates():
    """Test that exclusion rates are logged correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "test_report.json"
        
        log_exclusion_rates(
            total_initial=100,
            excluded_antibiotic=20,
            excluded_sleep=10,
            output_path=report_path
        )
        
        assert report_path.exists()
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert report['total_initial_sample_count'] == 100
        assert report['excluded_antibiotic_count'] == 20
        assert report['excluded_sleep_count'] == 10
        assert report['excluded_count'] == 30
        assert report['exclusion_proportion'] == 0.30
