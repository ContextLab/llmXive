"""
Tests for the validator module (T008c).
"""
import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Adjust imports to match project structure if running from root
# Assuming tests are run via pytest from the project root
import sys
sys.path.insert(0, 'code')

from validator import check_sample_count, run_validation, MIN_SAMPLE_THRESHOLD, FALLBACK_K

@pytest.fixture
def sample_df_large():
    """Create a dataframe with > 300 rows."""
    return pd.DataFrame({
        'layer_id': range(350),
        'utility_score': [0.5] * 350
    })

@pytest.fixture
def sample_df_small():
    """Create a dataframe with < 300 rows."""
    return pd.DataFrame({
        'layer_id': range(100),
        'utility_score': [0.5] * 100
    })

@pytest.fixture
def sample_df_empty():
    """Create an empty dataframe."""
    return pd.DataFrame(columns=['layer_id', 'utility_score'])

def test_check_sample_count_large(sample_df_large):
    result = check_sample_count(sample_df_large)
    assert result['valid'] is True
    assert result['sample_count'] == 350
    assert result['fallback_triggered'] is False
    assert result['fallback_reason'] is None
    assert result['k_value'] is None

def test_check_sample_count_small(sample_df_small):
    result = check_sample_count(sample_df_small)
    assert result['valid'] is False
    assert result['sample_count'] == 100
    assert result['fallback_triggered'] is True
    assert result['fallback_reason'] is not None
    assert result['k_value'] == FALLBACK_K

def test_check_sample_count_empty(sample_df_empty):
    result = check_sample_count(sample_df_empty)
    assert result['valid'] is False
    assert result['sample_count'] == 0
    assert result['fallback_triggered'] is True
    assert result['fallback_reason'] == "Empty dataset"
    assert result['k_value'] == FALLBACK_K

def test_run_validation_writes_file(sample_df_small, tmp_path):
    # Create a temporary input file
    input_file = tmp_path / "utility_labels.csv"
    sample_df_small.to_csv(input_file, index=False)
    
    output_file = tmp_path / "validation_status.json"
    
    # Run validation
    result = run_validation(str(input_file), str(output_file))
    
    # Verify result
    assert result['fallback_triggered'] is True
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        saved_result = json.load(f)
    
    assert saved_result == result