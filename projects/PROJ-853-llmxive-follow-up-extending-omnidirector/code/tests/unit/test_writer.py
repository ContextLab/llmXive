"""
Unit tests for T011: Writer module.
"""
import os
import json
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from data.writer import write_filtered_dataset, serialize_grid_points, serialize_matrix, calculate_sha256

def test_serialize_grid_points():
    points = np.array([[10, 20], [30, 40]])
    result = serialize_grid_points(points)
    expected = json.dumps(points.tolist())
    assert result == expected

def test_serialize_grid_points_empty():
    result = serialize_grid_points(np.array([]).reshape(0, 2))
    assert result == "[]"

def test_serialize_matrix():
    mat = np.eye(3)
    result = serialize_matrix(mat)
    expected = json.dumps(mat.tolist())
    assert result == expected

def test_write_filtered_dataset_creates_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_output.csv"
        checksum_path = Path(tmpdir) / "test_output.csv.sha256"
        
        df = pd.DataFrame({
            'sequence_id': ['seq1'],
            'frame_id': [1],
            'radial_motion_deg': [20.0],
            'z_velocity': [0.2],
            'grid_points_2d': [[10, 10]],
            'R_matrix': [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            't_vector': [0.0, 0.0, 0.0],
            'randomized_depth': [True]
        })
        
        # Temporarily override global paths for test
        import data.writer as writer_module
        original_output = writer_module.OUTPUT_PATH
        original_checksum = writer_module.CHECKSUM_PATH
        
        writer_module.OUTPUT_PATH = output_path
        writer_module.CHECKSUM_PATH = checksum_path
        
        try:
            write_filtered_dataset(df)
            assert output_path.exists()
            assert checksum_path.exists()
            
            # Verify content
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == 1
            assert loaded_df.iloc[0]['sequence_id'] == 'seq1'
            assert loaded_df.iloc[0]['randomized_depth'] == True
        finally:
            writer_module.OUTPUT_PATH = original_output
            writer_module.CHECKSUM_PATH = original_checksum

def test_write_empty_dataset():
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "empty.csv"
        checksum_path = Path(tmpdir) / "empty.csv.sha256"
        
        import data.writer as writer_module
        original_output = writer_module.OUTPUT_PATH
        original_checksum = writer_module.CHECKSUM_PATH
        
        writer_module.OUTPUT_PATH = output_path
        writer_module.CHECKSUM_PATH = checksum_path
        
        try:
            empty_df = pd.DataFrame()
            write_filtered_dataset(empty_df)
            
            assert output_path.exists()
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == 0
            # Check headers exist
            expected_cols = ['sequence_id', 'frame_id', 'radial_motion_deg', 'z_velocity', 'grid_points_2d', 'R_matrix', 't_vector', 'randomized_depth']
            assert list(loaded_df.columns) == expected_cols
        finally:
            writer_module.OUTPUT_PATH = original_output
            writer_module.CHECKSUM_PATH = original_checksum