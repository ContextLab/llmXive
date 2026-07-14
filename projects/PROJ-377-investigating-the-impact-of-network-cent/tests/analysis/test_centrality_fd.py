import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

from analysis.centrality import calculate_mean_fd, run_fd_analysis

@pytest.fixture
def temp_fd_dir():
    """Create a temporary directory with mock fMRIPrep confounds files."""
    temp_root = Path(tempfile.mkdtemp())
    base_dir = temp_root / "data" / "processed" / "fmriprep"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock subject directories and confounds files
    subjects = ["sub-01", "sub-02", "sub-03"]
    for subj in subjects:
        subj_dir = base_dir / subj
        subj_dir.mkdir(exist_ok=True)
        
        confounds_path = subj_dir / "desc-confounds_timeseries.tsv"
        # Create a mock TSV with framewise_displacement column
        mock_data = {
            'framewise_displacement': [0.1, 0.2, 0.15, 0.3, 0.25],
            'trans_x': [0.0, 0.0, 0.0, 0.0, 0.0],
            'trans_y': [0.0, 0.0, 0.0, 0.0, 0.0],
            'trans_z': [0.0, 0.0, 0.0, 0.0, 0.0],
            'rot_x': [0.0, 0.0, 0.0, 0.0, 0.0],
            'rot_y': [0.0, 0.0, 0.0, 0.0, 0.0],
            'rot_z': [0.0, 0.0, 0.0, 0.0, 0.0]
        }
        df = pd.DataFrame(mock_data)
        df.to_csv(confounds_path, sep='\t', index=False)
    
    yield base_dir
    
    # Cleanup
    shutil.rmtree(temp_root)

def test_calculate_mean_fd(temp_fd_dir):
    """Test that calculate_mean_fd correctly computes the mean FD."""
    subject_id = "sub-01"
    confounds_path = temp_fd_dir / subject_id / "desc-confounds_timeseries.tsv"
    
    mean_fd = calculate_mean_fd(subject_id, confounds_path)
    
    # Expected mean of [0.1, 0.2, 0.15, 0.3, 0.25]
    expected_mean = np.mean([0.1, 0.2, 0.15, 0.3, 0.25])
    
    assert isinstance(mean_fd, float)
    assert abs(mean_fd - expected_mean) < 1e-6

def test_run_fd_analysis(temp_fd_dir):
    """Test the full pipeline for FD analysis."""
    output_dir = Path(tempfile.mkdtemp())
    
    try:
        df = run_fd_analysis(output_dir, temp_fd_dir)
        
        # Check output file exists
        output_path = output_dir / "fd_mean.csv"
        assert output_path.exists()
        
        # Check dataframe content
        assert 'subject_id' in df.columns
        assert 'mean_fd' in df.columns
        assert len(df) == 3
        
        # Verify specific values
        sub01_row = df[df['subject_id'] == 'sub-01']
        assert not sub01_row.empty
        assert abs(sub01_row['mean_fd'].values[0] - np.mean([0.1, 0.2, 0.15, 0.3, 0.25])) < 1e-6
        
    finally:
        shutil.rmtree(output_dir)

def test_missing_confounds_file():
    """Test behavior when confounds file is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_path = Path(tmpdir) / "missing.tsv"
        with pytest.raises(FileNotFoundError):
            calculate_mean_fd("sub-99", missing_path)

def test_nan_handling(temp_fd_dir):
    """Test handling of NaN values in FD column."""
    subject_id = "sub-02"
    confounds_path = temp_fd_dir / subject_id / "desc-confounds_timeseries.tsv"
    
    # Inject NaN into the file temporarily for this test
    df = pd.read_csv(confounds_path, sep='\t')
    df.loc[0, 'framewise_displacement'] = np.nan
    df.to_csv(confounds_path, sep='\t', index=False)
    
    mean_fd = calculate_mean_fd(subject_id, confounds_path)
    
    # Should calculate mean of remaining non-NaN values
    expected = np.mean([0.2, 0.15, 0.3, 0.25])
    assert abs(mean_fd - expected) < 1e-6
