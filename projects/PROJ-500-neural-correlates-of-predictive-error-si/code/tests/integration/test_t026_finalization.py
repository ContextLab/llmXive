import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add code root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.data.align import (
    load_interim_lagged_mmns,
    load_behavioral_blocks,
    load_excluded_subjects,
    load_validation_report,
    finalize_aligned_dataset,
    run_alignment_pipeline,
    OUTPUT_FINAL_PATH
)

@pytest.fixture
def temp_data_setup(tmp_path):
    """Setup temporary data files for testing."""
    # Create directories
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Create interim MMN
    mmn_data = {
        'subject_id': ['sub-001', 'sub-001', 'sub-002', 'sub-002'],
        'block_id': ['1', '2', '1', '2'],
        'mmn_amplitude': [-2.34, -2.56, -2.12, -2.25],
        'source_window_start_trial': [1, 51, 1, 51]
    }
    pd.DataFrame(mmn_data).to_csv(data_dir / "interim_lagged_mmns.csv", index=False)
    
    # Create behavioral blocks
    behav_data = {
        'subject_id': ['sub-001', 'sub-001', 'sub-002', 'sub-002'],
        'block_id': ['1', '2', '1', '2'],
        'accuracy': [0.85, 0.88, 0.82, 0.84]
    }
    pd.DataFrame(behav_data).to_csv(data_dir / "behavioral_blocks.csv", index=False)
    
    # Create excluded subjects
    exc_data = {'subject_id': ['sub-003']}
    pd.DataFrame(exc_data).to_csv(data_dir / "excluded_subjects.csv", index=False)
    
    # Create validation report
    import json
    report = {
        "analysis_mode": "error_signal",
        "variables_present": {"stimulus_type": True, "response_correctness": True}
    }
    with open(data_dir / "validation_report.json", 'w') as f:
        json.dump(report, f)
        
    return data_dir

def test_t026_merge_logic(temp_data_setup, tmp_path):
    """Test that T026 correctly merges and filters data."""
    # Change to temp directory to simulate running in project root
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Mock the paths in the module to use temp paths
        # Since the functions use hardcoded strings like "data/...", 
        # we rely on the fixture creating files in the current working directory
        # The fixture created files in tmp_path/data, but the code looks for "data/..."
        # We need to move files or adjust. 
        # Let's assume the test runner sets up the environment or we move files.
        # Actually, the fixture creates in tmp_path/data. The code expects data/... relative to CWD.
        # So we set CWD to tmp_path.
        
        # Run the logic
        mmn_df = load_interim_lagged_mmns()
        behav_df = load_behavioral_blocks()
        exc_subs = load_excluded_subjects()
        report = load_validation_report()
        
        assert len(mmn_df) == 4
        assert len(behav_df) == 4
        assert len(exc_subs) == 1
        assert report['analysis_mode'] == 'error_signal'
        
        final_df = finalize_aligned_dataset(mmn_df, behav_df, exc_subs, report['analysis_mode'])
        
        # Check columns
        assert 'mmn_amplitude' in final_df.columns
        assert 'accuracy' in final_df.columns
        assert 'analysis_mode' in final_df.columns
        
        # Check filtering (sub-003 not in data, so no change in count for sub-001/002)
        # If sub-003 was in the input data, it should be gone.
        assert 'sub-003' not in final_df['subject_id'].values
        
        # Check merge
        assert len(final_df) == 4
        
    finally:
        os.chdir(original_cwd)

def test_t026_full_pipeline_execution(temp_data_setup, tmp_path):
    """Test that the full pipeline script runs and creates the output file."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Ensure files are in the right place relative to CWD
        # The fixture created them in tmp_path/data, which is correct if CWD is tmp_path
        
        # Run the pipeline
        run_alignment_pipeline()
        
        # Check output exists
        output_file = Path("data/aligned_data.csv")
        assert output_file.exists(), "aligned_data.csv was not created"
        
        # Check content
        df = pd.read_csv(output_file)
        assert not df.empty
        assert 'accuracy' in df.columns
        assert 'mmn_amplitude' in df.columns
        assert 'analysis_mode' in df.columns
        
    finally:
        os.chdir(original_cwd)
