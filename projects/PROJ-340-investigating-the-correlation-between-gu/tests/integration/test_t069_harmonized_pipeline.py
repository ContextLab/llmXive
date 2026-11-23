import os
import json
import pytest
import pandas as pd
from pathlib import Path
import sys

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from main import run_ingestion_and_validation, setup_paths
from ingest import load_harmonized_data, HarmonizedDataNotFoundError

@pytest.fixture
def temp_harmonized_data(tmp_path):
    """Create a mock harmonized parquet file for testing."""
    setup_paths()
    data = {
        'subject_id': [1, 2, 3, 4, 5],
        'Bacteroides': [100, 120, 90, 110, 105],
        'Firmicutes': [50, 60, 45, 55, 52],
        'SWS duration': [4.5, 5.0, 4.2, 4.8, 4.6],
        'REM duration': [1.5, 1.8, 1.4, 1.7, 1.6]
    }
    df = pd.DataFrame(data)
    path = tmp_path / 'harmonized_data.parquet'
    df.to_parquet(path)
    return str(path), df

@pytest.fixture
def mock_config(temp_harmonized_data):
    return {
        'schema_path': 'specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml',
        'required_vars_path': 'data/config/required_variables.yaml',
        'harmonized_path': temp_harmonized_data[0],
        'state_file': 'state/projects/test_state.yaml',
        'seed': 42
    }

def test_harmonized_data_load_success(temp_harmonized_data):
    """Test that harmonized data loads correctly."""
    path, expected_df = temp_harmonized_data
    df, meta = load_harmonized_data(path, 'state/projects/test_state.yaml')
    assert df is not None
    assert len(df) == 5
    assert 'subject_id' in df.columns

def test_harmonized_data_missing_raises_error(tmp_path):
    """Test that missing harmonized data raises specific error."""
    with pytest.raises(HarmonizedDataNotFoundError):
        load_harmonized_data('non_existent_path.parquet', 'state/projects/test_state.yaml')

def test_pipeline_uses_harmonized_data_when_present(mock_config, temp_harmonized_data, tmp_path):
    """
    T069 Test: Verify that main.py logic detects harmonized_data.parquet
    and proceeds without halting, generating the required reports.
    """
    # Ensure the harmonized file exists at the expected config path
    # (mock_config already points to temp_harmonized_data[0])
    
    # Run ingestion
    df, source_type = run_ingest_and_validation(mock_config, mode='real')
    
    assert source_type == 'harmonized', f"Expected 'harmonized', got {source_type}"
    assert df is not None
    assert len(df) == 5
    
    # Verify artifacts were created
    assert Path('data/results/harmonization_report.json').exists(), "harmonization_report.json missing"
    assert Path('data/results/real_data_analysis_report.json').exists(), "real_data_analysis_report.json missing"
    
    # Verify content of harmonization report
    with open('data/results/harmonization_report.json', 'r') as f:
        report = json.load(f)
    
    assert report['status'] == 'SUCCESS'
    assert report['source_type'] == 'harmonized_multi_cohort'
    
    # Verify content of real data analysis report
    with open('data/results/real_data_analysis_report.json', 'r') as f:
        analysis_report = json.load(f)
    
    assert analysis_report['status'] == 'SUCCESS'
    assert analysis_report['data_loaded'] == True
    
    # Cleanup state file
    if Path('state/projects/test_state.yaml').exists():
        Path('state/projects/test_state.yaml').unlink()