import os
import sys
import pytest
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from config import get_project_root
from generate_ingested_cohort import calculate_file_checksum, save_state_entry

@pytest.mark.integration
def test_t018_output_generation():
    """
    Test that T018 generates the expected parquet file and updates state.yaml.
    This test assumes the raw data has been downloaded by T013.
    """
    project_root = get_project_root()
    output_path = project_root / 'data' / 'processed' / 'ingested_cohort.parquet'
    state_path = project_root / 'state.yaml'

    # Run the main logic of T018
    # We import and call main, but we need to be careful about side effects.
    # For this test, we assume the data is already present.
    from generate_ingested_cohort import main
    
    try:
        main()
    except FileNotFoundError as e:
        # If raw data is missing, the test environment might not be set up.
        # We skip if raw data is missing, but the task requires the file to exist.
        if "Could not locate MSD dataset" in str(e):
            pytest.skip("Raw MSD dataset not found. T013 must run first.")
        raise

    # Verify file existence
    assert output_path.exists(), f"Output file {output_path} does not exist."

    # Verify file is not empty
    file_size = output_path.stat().st_size
    assert file_size > 0, f"Output file {output_path} is empty."

    # Verify it is a valid parquet file
    try:
        df = pd.read_parquet(output_path)
        assert len(df) > 0, "Output parquet file has no rows."
        
        # Check for required columns based on US1
        required_cols = ['adolescent_exposure_score', 'residualized_exposure_score']
        for col in required_cols:
            assert col in df.columns, f"Missing required column: {col}"
            
    except Exception as e:
        pytest.fail(f"Failed to read or validate parquet file: {e}")

    # Verify state.yaml update
    assert state_path.exists(), "state.yaml does not exist."
    
    import yaml
    with open(state_path, 'r') as f:
        state_data = yaml.safe_load(f)
    
    assert 'files' in state_data, "state.yaml missing 'files' key."
    assert 'ingested_cohort.parquet' in state_data['files'], "ingested_cohort.parquet not in state.yaml."
    
    file_entry = state_data['files']['ingested_cohort.parquet']
    assert 'checksum' in file_entry, "Checksum missing in state entry."
    assert 'generated_at' in file_entry, "generated_at missing in state entry."
    
    # Verify checksum matches
    actual_checksum = calculate_file_checksum(str(output_path))
    assert file_entry['checksum'] == actual_checksum, "Checksum in state.yaml does not match file."
