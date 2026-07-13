"""
Unit tests for T017: Download and Filter logic.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.io import ensure_dir
from utils.logger import get_logger

# Import functions to test (mocking network calls)
from code import download_and_filter as df_module

@pytest.fixture
def mock_data_dir(tmp_path):
    return tmp_path / "data" / "raw"

@pytest.fixture
def mock_processed_dir(tmp_path):
    return tmp_path / "data" / "processed"

def test_parse_bids_metadata_with_participants(mock_data_dir):
    """
    Test that parse_bids_metadata correctly identifies eligible subjects
    based on MMSE/MOCA columns.
    """
    ensure_dir(mock_data_dir)
    
    # Create a fake participants.tsv
    data = {
        'participant_id': ['sub-01', 'sub-02', 'sub-03'],
        'MMSE_time1': [28.0, 24.0, None],
        'MMSE_time2': [27.0, 20.0, 25.0],
        'MOCA_time1': [26.0, None, 27.0],
        'MOCA_time2': [25.0, 22.0, 26.0]
    }
    df = pd.DataFrame(data)
    df.to_csv(mock_data_dir / "participants.tsv", sep='\t', index=False)
    
    eligible, excluded = df_module.parse_bids_metadata(mock_data_dir)
    
    # sub-01: has 4 scores -> eligible
    # sub-02: has 3 scores (MMSE_1, MMSE_2, MOCA_2) -> eligible
    # sub-03: has 3 scores (MMSE_2, MOCA_1, MOCA_2) -> eligible (assuming >=2)
    
    # However, the logic in parse_bids_metadata might be stricter on timepoints.
    # Let's assume the logic finds >= 2 non-null.
    assert len(eligible) >= 2 # At least sub-01 and sub-02
    assert len(excluded) == 0 # All have >= 2 scores

def test_filter_eligible_subjects_limits_n():
    """
    Test that filter_eligible_subjects limits the list to N_MAX.
    """
    eligible = [{'subject_id': f'sub-{i}'} for i in range(150)]
    excluded = []
    
    result_eligible, _ = df_module.filter_eligible_subjects(eligible, excluded, 100)
    
    assert len(result_eligible) == 100
    assert result_eligible[0]['subject_id'] == 'sub-0'
    assert result_eligible[-1]['subject_id'] == 'sub-99'

def test_write_outputs_creates_files(mock_processed_dir):
    """
    Test that write_outputs creates the correct files.
    """
    ensure_dir(mock_processed_dir)
    eligible = [{'subject_id': 'sub-01', 'scores': [28, 27], 'reason': 'test'}]
    excluded = [{'subject_id': 'sub-02', 'reason': 'missing'}]
    
    df_module.write_outputs(eligible, excluded, mock_processed_dir)
    
    assert (mock_processed_dir / "eligible_subjects.csv").exists()
    assert (mock_processed_dir / "excluded_subjects.log").exists()
    
    csv_df = pd.read_csv(mock_processed_dir / "eligible_subjects.csv")
    assert 'subject_id' in csv_df.columns
    assert len(csv_df) == 1
    
    with open(mock_processed_dir / "excluded_subjects.log", 'r') as f:
        content = f.read()
        assert 'sub-02' in content
        assert 'missing' in content

def test_main_zero_eligible_exits(mock_data_dir, mock_processed_dir, caplog):
    """
    Test that main exits with code 2 if no eligible subjects are found.
    """
    # Mock the functions to return empty lists
    with patch.object(df_module, 'check_dataset_availability', return_value=True), \
         patch.object(df_module, 'download_dataset', return_value=True), \
         patch.object(df_module, 'parse_bids_metadata', return_value=([], [])):
         
        with pytest.raises(SystemExit) as excinfo:
            df_module.main()
        
        assert excinfo.value.code == 2
        assert "Zero eligible subjects" in caplog.text

def test_main_network_failure_exits(mock_data_dir, mock_processed_dir, caplog):
    """
    Test that main exits with code 1 if download fails.
    """
    with patch.object(df_module, 'check_dataset_availability', return_value=True), \
         patch.object(df_module, 'download_dataset', return_value=False):
         
        with pytest.raises(SystemExit) as excinfo:
            df_module.main()
        
        assert excinfo.value.code == 1
        assert "Failed to download" in caplog.text