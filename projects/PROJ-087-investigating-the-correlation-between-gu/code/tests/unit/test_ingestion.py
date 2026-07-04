import pytest
import pandas as pd
import os
from unittest.mock import patch, MagicMock
from src.ingestion import verify_schema, filter_antibiotic_use, filter_sleep_data, fetch_sample_headers, log_exclusion_rates
import json
import tempfile

@pytest.fixture
def sample_df():
    """Create a sample dataframe for testing."""
    return pd.DataFrame({
        'sample_id': ['s1', 's2', 's3', 's4', 's5'],
        'antibiotic_use_last_3m': [True, False, True, False, False],
        'sleep_efficiency': [0.8, 0.9, 0.7, None, 0.85],
        'sleep_duration_hours': [7.0, 8.0, 6.0, 7.5, None],
        'other_col': [1, 2, 3, 4, 5]
    })

def test_antibiotic_exclusion_logic(sample_df):
    """Test that samples with antibiotic_use_last_3m=True are filtered out."""
    filtered_df, excluded_count = filter_antibiotic_use(sample_df)
    
    # Expected: Keep s2, s4, s5 (antibiotic_use is False)
    # Exclude s1, s3 (antibiotic_use is True)
    assert len(filtered_df) == 3
    assert excluded_count == 2
    assert all(filtered_df['antibiotic_use_last_3m'] == False)
    assert 's1' not in filtered_df['sample_id'].values
    assert 's3' not in filtered_df['sample_id'].values

def test_sleep_data_validation(sample_df):
    """Test that samples with null sleep_efficiency or sleep_duration_hours are filtered."""
    # First, ensure we have data to test on (resetting for clarity)
    # Note: In a real pipeline, this would run after antibiotic filtering
    filtered_df, excluded_count = filter_sleep_data(sample_df)
    
    # Expected: 
    # s1: 0.8, 7.0 -> Keep
    # s2: 0.9, 8.0 -> Keep
    # s3: 0.7, 6.0 -> Keep
    # s4: None, 7.5 -> Exclude (null efficiency)
    # s5: 0.85, None -> Exclude (null duration)
    assert len(filtered_df) == 3
    assert excluded_count == 2
    assert filtered_df['sleep_efficiency'].notna().all()
    assert filtered_df['sleep_duration_hours'].notna().all()

def test_schema_verification_success():
    """Test schema verification with mock headers containing required columns."""
    mock_headers = ['sample_id', 'antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    
    with patch('src.ingestion.fetch_sample_headers', return_value=mock_headers):
        result = verify_schema('http://fake.url', ['antibiotic_use_last_3m', 'sleep_efficiency'])
        assert result is True

def test_schema_verification_missing_columns():
    """Test schema verification fails when columns are missing."""
    mock_headers = ['sample_id', 'other_col']
    
    with patch('src.ingestion.fetch_sample_headers', return_value=mock_headers):
        result = verify_schema('http://fake.url', ['antibiotic_use_last_3m'])
        assert result is False

def test_schema_verification_unreachable():
    """Test schema verification fails when URL is unreachable."""
    with patch('src.ingestion.fetch_sample_headers', return_value=None):
        result = verify_schema('http://unreachable.url', ['col'])
        assert result is False

def test_log_exclusion_rates():
    """Test that log_exclusion_rates creates a valid JSON report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = os.path.join(tmpdir, 'test_report.json')
        total_initial = 100
        excluded_antibiotic = 10
        excluded_sleep = 5
        
        log_exclusion_rates(total_initial, excluded_antibiotic, excluded_sleep, report_path)
        
        assert os.path.exists(report_path)
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert report['total_initial_sample_count'] == 100
        assert report['excluded_count'] == 15
        assert report['exclusion_proportion'] == 0.15
        assert report['breakdown']['excluded_antibiotic'] == 10
        assert report['breakdown']['excluded_sleep_data'] == 5