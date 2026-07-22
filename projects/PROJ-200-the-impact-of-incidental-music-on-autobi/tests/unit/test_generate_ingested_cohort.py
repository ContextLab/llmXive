"""
Unit tests for generate_ingested_cohort.py (T018).
"""
import os
import tempfile
import pytest
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
import hashlib
import yaml

# Mock the config and utils for testing
import sys
from unittest.mock import patch, MagicMock

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_calculate_file_checksum(temp_dir):
    """Test that calculate_file_checksum returns a valid SHA-256 hex string."""
    from generate_ingested_cohort import calculate_file_checksum
    
    # Create a test file
    test_file = temp_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    checksum = calculate_file_checksum(test_file)
    
    # Verify length (SHA-256 is 64 hex chars)
    assert len(checksum) == 64
    # Verify it's a valid hex string
    int(checksum, 16)
    
    # Verify against known hash
    expected = hashlib.sha256(test_content).hexdigest()
    assert checksum == expected

def test_save_state_entry_updates_yaml(temp_dir):
    """Test that save_state_entry correctly updates state.yaml."""
    from generate_ingested_cohort import save_state_entry
    from state_manager import load_state, save_state, initialize_state
    
    # Setup a mock state file
    state_file = temp_dir / "state.yaml"
    initialize_state(state_file)
    
    # Mock the get_project_root to return temp_dir
    with patch('generate_ingested_cohort.get_project_root', return_value=temp_dir):
        with patch('generate_ingested_cohort.save_state') as mock_save:
            # Create a dummy file
            dummy_file = temp_dir / "dummy.parquet"
            dummy_file.write_bytes(b"dummy")
            
            save_state_entry(dummy_file, "abc123", "processed_data")
            
            mock_save.assert_called_once()

def test_main_failure_missing_intermediate(temp_dir):
    """Test that main exits with error if intermediate CSV is missing."""
    from generate_ingested_cohort import main
    
    # Setup paths in temp_dir
    with patch('generate_ingested_cohort.get_project_root', return_value=temp_dir):
        with patch('generate_ingested_cohort.setup_logging'):
            with patch('sys.exit') as mock_exit:
                with patch('generate_ingested_cohort.logger') as mock_logger:
                    # Ensure intermediate file does not exist
                    (temp_dir / "data" / "processed").mkdir(parents=True, exist_ok=True)
                    (temp_dir / "data" / "processed" / "intermediate_cohort.csv").unlink(missing_ok=True)
                    
                    main()
                    
                    mock_logger.error.assert_called()
                    mock_exit.assert_called_once_with(1)

def test_main_failure_missing_columns(temp_dir):
    """Test that main exits with error if required columns are missing."""
    from generate_ingested_cohort import main
    
    # Create a mock intermediate CSV with missing columns
    csv_path = temp_dir / "data" / "processed" / "intermediate_cohort.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_bad = pd.DataFrame({'track_id': [1, 2]}) # Missing other required cols
    df_bad.to_csv(csv_path, index=False)
    
    with patch('generate_ingested_cohort.get_project_root', return_value=temp_dir):
        with patch('generate_ingested_cohort.setup_logging'):
            with patch('sys.exit') as mock_exit:
                with patch('generate_ingested_cohort.logger') as mock_logger:
                    main()
                    
                    mock_logger.error.assert_called()
                    mock_exit.assert_called_once_with(1)

def test_main_success_creates_parquet(temp_dir):
    """Test that main successfully creates the parquet file and updates state."""
    from generate_ingested_cohort import main
    
    # Create a valid intermediate CSV
    csv_path = temp_dir / "data" / "processed" / "intermediate_cohort.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_good = pd.DataFrame({
        'track_id': [1, 2, 3],
        'adolescent_exposure_score': [0.5, 0.6, 0.7],
        'residualized_exposure_score': [0.1, 0.2, 0.3],
        'overall_popularity_score': [10, 20, 30]
    })
    df_good.to_csv(csv_path, index=False)
    
    output_path = temp_dir / "data" / "processed" / "ingested_cohort.parquet"
    
    # Mock dependencies
    with patch('generate_ingested_cohort.get_project_root', return_value=temp_dir):
        with patch('generate_ingested_cohort.setup_logging'):
            with patch('generate_ingested_cohort.save_state'):
                with patch('generate_ingested_cohort.logger'):
                    main()
                    
                    assert output_path.exists()
                    
                    # Verify parquet content
                    df_loaded = pd.read_parquet(output_path)
                    assert df_loaded.shape == df_good.shape
                    assert list(df_loaded.columns) == list(df_good.columns)
