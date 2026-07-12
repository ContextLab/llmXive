"""
Unit tests for dataset fetcher.
Tests the synthetic data generation logic.
"""
import os
import json
import zipfile
import tempfile
import pandas as pd
from pathlib import Path
import pytest
import numpy as np

# Mock the HF fetch to always fail for testing
import code.data.dataset_fetcher as fetcher_module

@pytest.fixture
def mock_hf_fail(monkeypatch):
    """Mock HuggingFace fetch to always return None."""
    def mock_fetch():
        return None
    monkeypatch.setattr(fetcher_module, 'attempt_hf_fetch', mock_fetch)

def test_synthetic_data_schema(mock_hf_fail, tmp_path):
    """Test that synthetic data generation produces correct schema."""
    # Temporarily override paths
    original_raw = fetcher_module.RAW_DIR
    original_proc = fetcher_module.PROCESSED_DIR
    
    fetcher_module.RAW_DIR = tmp_path / "raw"
    fetcher_module.PROCESSED_DIR = tmp_path / "processed"
    fetcher_module.RAW_DIR.mkdir()
    fetcher_module.PROCESSED_DIR.mkdir()
    
    try:
        zip_path = fetcher_module.generate_synthetic_data()
        
        # Verify zip file exists
        assert os.path.exists(zip_path)
        
        # Extract and verify contents
        with zipfile.ZipFile(zip_path, 'r') as zf:
            assert 'filtered_sequences.csv' in zf.namelist()
            assert 'metadata.json' in zf.namelist()
            
            # Load CSV
            csv_content = zf.read('filtered_sequences.csv').decode('utf-8')
            df = pd.read_csv(pd.io.common.BytesIO(csv_content.encode()))
            
            # Check required columns
            required_cols = [
                'sequence_id', 'frame_id', 'radial_motion_deg', 
                'z_velocity', 'grid_points_2d', 'R_matrix', 
                't_vector', 'randomized_depth'
            ]
            assert list(df.columns) == required_cols
            
            # Check data types and constraints
            assert len(df) > 0
            assert df['radial_motion_deg'].min() >= 0
            assert df['randomized_depth'].dtype == 'bool'
            
            # Verify grid_points_2d is a valid JSON list
            sample_points = df['grid_points_2d'].iloc[0]
            points_list = json.loads(sample_points)
            assert isinstance(points_list, list)
            assert len(points_list) > 0
            for point in points_list[:3]:
                assert isinstance(point, list)
                assert len(point) == 2
                
    finally:
        # Restore original paths
        fetcher_module.RAW_DIR = original_raw
        fetcher_module.PROCESSED_DIR = original_proc

def test_deterministic_synthetic(mock_hf_fail, tmp_path):
    """Test that synthetic generation is deterministic."""
    original_raw = fetcher_module.RAW_DIR
    original_proc = fetcher_module.PROCESSED_DIR
    
    fetcher_module.RAW_DIR = tmp_path / "raw1"
    fetcher_module.PROCESSED_DIR = tmp_path / "proc1"
    fetcher_module.RAW_DIR.mkdir()
    fetcher_module.PROCESSED_DIR.mkdir()
    
    zip_path1 = fetcher_module.generate_synthetic_data()
    
    # Reset and generate again
    fetcher_module.RAW_DIR = tmp_path / "raw2"
    fetcher_module.PROCESSED_DIR = tmp_path / "proc2"
    fetcher_module.RAW_DIR.mkdir()
    fetcher_module.PROCESSED_DIR.mkdir()
    
    zip_path2 = fetcher_module.generate_synthetic_data()
    
    try:
        # Compare CSV contents
        with zipfile.ZipFile(zip_path1, 'r') as zf1:
            csv1 = zf1.read('filtered_sequences.csv')
        with zipfile.ZipFile(zip_path2, 'r') as zf2:
            csv2 = zf2.read('filtered_sequences.csv')
        
        assert csv1 == csv2
    finally:
        fetcher_module.RAW_DIR = original_raw
        fetcher_module.PROCESSED_DIR = original_proc