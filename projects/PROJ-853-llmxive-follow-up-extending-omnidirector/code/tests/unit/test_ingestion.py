import os
import json
import tempfile
import zipfile
import pandas as pd
import pytest
from pathlib import Path
import sys

# Add code to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.ingestion import (
    apply_geometric_filter, 
    create_grid_frames, 
    load_dataset_from_zip, 
    validate_schema,
    RADIAL_MOTION_THRESHOLD_DEG,
    Z_VELOCITY_THRESHOLD
)
from data.models import GridFrame, CameraPose
import numpy as np

def make_test_df(num_rows=10):
    """Create a mock DataFrame matching the T007/T008 schema."""
    data = {
        'sequence_id': ['seq1'] * num_rows,
        'frame_id': list(range(num_rows)),
        'radial_motion_deg': [10.0] * num_rows, # Default low motion
        'z_velocity': [0.05] * num_rows,       # Default low velocity
        'grid_points_2d': ['[[0,0],[100,0],[100,100],[0,100]]'] * num_rows,
        'R_matrix': ['[[1,0,0],[0,1,0],[0,0,1]]'] * num_rows,
        't_vector': ['[0,0,0]'] * num_rows,
        'randomized_depth': [False] * num_rows
    }
    return pd.DataFrame(data)

def create_temp_zip(df, filename="test_data.zip"):
    """Create a temporary zip file containing the DataFrame as CSV."""
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.close(fd)
    
    csv_fd, csv_path = tempfile.mkstemp(suffix=".csv")
    os.close(csv_fd)
    df.to_csv(csv_path, index=False)
    
    with zipfile.ZipFile(path, 'w') as zf:
        zf.write(csv_path, 'data.csv')
    
    os.remove(csv_path)
    return path

def test_validate_schema():
    df = make_test_df()
    assert validate_schema(df) is True

def test_validate_schema_missing_column():
    df = make_test_df()
    df = df.drop(columns=['radial_motion_deg'])
    assert validate_schema(df) is False

def test_apply_geometric_filter_retained_by_radial():
    """Test that sequences with radial motion > 15 are retained."""
    df = make_test_df()
    # Set one frame to high radial motion
    df.loc[0, 'radial_motion_deg'] = 20.0
    
    frames = create_grid_frames(df)
    retained, excluded = apply_geometric_filter(frames)
    
    # All frames in seq1 should be retained because the sequence qualifies
    assert len(retained) == len(df)
    assert len(excluded) == 0

def test_apply_geometric_filter_retained_by_z_velocity():
    """Test that sequences with z_velocity > 0.1 are retained."""
    df = make_test_df()
    df.loc[0, 'z_velocity'] = 0.2
    
    frames = create_grid_frames(df)
    retained, excluded = apply_geometric_filter(frames)
    
    assert len(retained) == len(df)
    assert len(excluded) == 0

def test_apply_geometric_filter_excluded():
    """Test that sequences with low motion are excluded."""
    df = make_test_df()
    # All default values are below thresholds
    
    frames = create_grid_frames(df)
    retained, excluded = apply_geometric_filter(frames)
    
    assert len(retained) == 0
    assert len(excluded) == len(df)

def test_apply_geometric_filter_mixed_sequences():
    """Test filtering with multiple sequences, some retained, some excluded."""
    data = {
        'sequence_id': ['seq_retained'] * 5 + ['seq_excluded'] * 5,
        'frame_id': list(range(10)),
        'radial_motion_deg': [20.0] * 5 + [10.0] * 5,
        'z_velocity': [0.05] * 10,
        'grid_points_2d': ['[[0,0],[100,0],[100,100],[0,100]]'] * 10,
        'R_matrix': ['[[1,0,0],[0,1,0],[0,0,1]]'] * 10,
        't_vector': ['[0,0,0]'] * 10,
        'randomized_depth': [False] * 10
    }
    df = pd.DataFrame(data)
    
    frames = create_grid_frames(df)
    retained, excluded = apply_geometric_filter(frames)
    
    assert len(retained) == 5
    assert len(excluded) == 5
    assert all(f.sequence_id == 'seq_retained' for f in retained)
    assert all(f.sequence_id == 'seq_excluded' for f in excluded)

def test_integration_load_and_filter():
    """Integration test: create zip, load, filter."""
    df = make_test_df()
    df.loc[0, 'radial_motion_deg'] = 16.0 # Trigger retention
    
    zip_path = create_temp_zip(df)
    
    try:
        loaded_df = load_dataset_from_zip(zip_path)
        frames = create_grid_frames(loaded_df)
        retained, excluded = apply_geometric_filter(frames)
        
        assert len(retained) == len(df)
        assert len(excluded) == 0
    finally:
        os.remove(zip_path)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])