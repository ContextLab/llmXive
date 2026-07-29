"""
Unit tests for the writer module.
Tests serialization and CSV writing functionality.
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from data.writer import (
    serialize_grid_points,
    serialize_matrix,
    calculate_sha256,
    write_filtered_dataset
)
from data.models import GridFrame

def test_serialize_grid_points():
    """Test serialization of grid points."""
    points = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
    serialized = serialize_grid_points(points)
    deserialized = json.loads(serialized)
    assert deserialized == points

def test_serialize_grid_points_empty():
    """Test serialization of empty grid points."""
    serialized = serialize_grid_points([])
    assert json.loads(serialized) == []
    
    serialized_none = serialize_grid_points(None)
    assert json.loads(serialized_none) == []

def test_serialize_matrix():
    """Test serialization of rotation matrix."""
    matrix = np.eye(3)
    serialized = serialize_matrix(matrix)
    deserialized = np.array(json.loads(serialized))
    np.testing.assert_array_almost_equal(deserialized, matrix)

def test_write_filtered_dataset_creates_file():
    """Test that write_filtered_dataset creates the output file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_output.csv")
        
        # Create test grid frames
        frames = [
            GridFrame(
                sequence_id="seq1",
                frame_id=1,
                radial_motion_deg=20.0,
                z_velocity=0.2,
                grid_points_2d=[[10, 10], [20, 20]],
                R_matrix=np.eye(3),
                t_vector=np.array([0, 0, 1]),
                randomized_depth=False
            ),
            GridFrame(
                sequence_id="seq1",
                frame_id=2,
                radial_motion_deg=10.0,
                z_velocity=0.05,
                grid_points_2d=[[15, 15], [25, 25]],
                R_matrix=np.eye(3),
                t_vector=np.array([0, 0, 2]),
                randomized_depth=True
            )
        ]
        
        result = write_filtered_dataset(frames, output_path)
        
        assert os.path.exists(output_path)
        assert result['rows_written'] == 2
        assert 'checksum' in result
        
        # Verify CSV content
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert 'sequence_id' in df.columns
        assert 'grid_points_2d' in df.columns

def test_write_empty_dataset():
    """Test writing an empty dataset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "empty_output.csv")
        
        result = write_filtered_dataset([], output_path)
        
        assert os.path.exists(output_path)
        assert result['rows_written'] == 0
        
        # Verify CSV has headers only
        df = pd.read_csv(output_path)
        assert len(df) == 0
        assert 'sequence_id' in df.columns