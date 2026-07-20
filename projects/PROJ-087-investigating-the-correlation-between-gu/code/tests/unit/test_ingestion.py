import pytest
import pandas as pd
import os
from unittest.mock import patch, MagicMock
from src.ingestion import verify_schema, filter_antibiotic_use, filter_sleep_data, fetch_sample_headers, log_exclusion_rates
import json

@pytest.fixture
def sample_df():
    """Create a sample dataframe for testing."""
    return pd.DataFrame({
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5'],
        'antibiotic_use_last_3m': [False, True, False, None, True],
        'sleep_efficiency': [85.0, 78.0, None, 90.0, 82.0],
        'sleep_duration_hours': [7.5, 6.8, 8.0, None, 7.2],
        'other_data': [1, 2, 3, 4, 5]
    })

def test_antibiotic_exclusion_logic(sample_df):
    """Test that samples with antibiotic use are filtered out."""
    filtered_df = filter_antibiotic_use(sample_df)
    
    # Check that no samples with True antibiotic use remain
    assert filtered_df[filtered_df['antibiotic_use_last_3m'] == True].empty
    
    # Check that samples with False, None, or other values remain
    expected_count = 3  # S1 (False), S3 (False), S4 (None)
    assert len(filtered_df) == expected_count

def test_sleep_data_validation(sample_df):
    """Test that samples with missing sleep data are filtered out."""
    filtered_df = filter_sleep_data(sample_df)
    
    # Check that no samples with null sleep_efficiency or sleep_duration_hours remain
    assert filtered_df['sleep_efficiency'].notna().all()
    assert filtered_df['sleep_duration_hours'].notna().all()
    
    # Only S1 has both sleep metrics valid
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['sample_id'] == 'S1'

def test_schema_verification_success(sample_df):
    """Test successful schema verification with required columns."""
    required_columns = ['antibiotic_use_last_3m', 'sleep_efficiency', 'sleep_duration_hours']
    assert verify_schema(sample_df, required_columns) is True

def test_schema_verification_missing_columns(sample_df):
    """Test schema verification fails with missing columns."""
    required_columns = ['antibiotic_use_last_3m', 'sleep_efficiency', 'missing_column']
    assert verify_schema(sample_df, required_columns) is False

def test_log_exclusion_rates(tmp_path):
    """Test that exclusion rates are logged correctly."""
    output_path = tmp_path / "ingestion_report.json"
    initial_count = 100
    final_count = 80
    
    result = log_exclusion_rates(initial_count, final_count, str(output_path))
    
    assert result['total_initial_sample_count'] == initial_count
    assert result['excluded_count'] == 20
    assert result['exclusion_proportion'] == 0.2
    assert result['final_sample_count'] == final_count
    
    # Verify file was created and contains valid JSON
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
        assert data == result