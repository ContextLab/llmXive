"""
Integration tests for the end-to-end data pipeline on a single species subset.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from config import DATA_DIR, PROJECT_ROOT
from utils.data_utils import validate_coordinates, check_data_quality
from utils.spatial_blocks import create_spatial_blocks


def test_end_to_end_data_validation():
    """
    Integration test: Verify that data flows correctly through validation and 
    spatial blocking utilities.
    """
    # Create temporary directory for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        test_data_path = Path(tmpdir) / "test_occurrence.csv"
        
        # Create mock data
        np.random.seed(42)
        n_records = 50
        data = {
            'species': 'Buteo_jamaicensis',
            'latitude': np.random.uniform(25, 50, n_records),
            'longitude': np.random.uniform(-125, -70, n_records),
            'year': np.random.randint(1970, 2000, n_records)
        }
        df = pd.DataFrame(data)
        df.to_csv(test_data_path, index=False)
        
        # Load data
        loaded_df = pd.read_csv(test_data_path)
        
        # Validate coordinates
        valid_df = validate_coordinates(loaded_df)
        
        assert len(valid_df) == len(loaded_df), "All records should be valid"
        
        # Check data quality
        quality_report = check_data_quality(valid_df)
        
        assert quality_report['total_records'] == n_records
        assert quality_report['valid_coordinates'] == n_records
        
        # Apply spatial blocking
        blocked_df = create_spatial_blocks(valid_df, n_blocks=2)
        
        assert 'block_id' in blocked_df.columns
        assert blocked_df['block_id'].nunique() == 2


def test_coordinate_validation_edge_cases():
    """
    Integration test: Verify handling of invalid coordinates.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        test_data_path = Path(tmpdir) / "test_invalid.csv"
        
        # Create data with some invalid coordinates
        data = {
            'species': 'Buteo_jamaicensis',
            'latitude': [30.0, 95.0, -10.0, 45.0],  # 95 and -10 are invalid
            'longitude': [-100.0, -110.0, -120.0, -90.0]
        }
        df = pd.DataFrame(data)
        df.to_csv(test_data_path, index=False)
        
        loaded_df = pd.read_csv(test_data_path)
        valid_df = validate_coordinates(loaded_df)
        
        # Should only have 2 valid records
        assert len(valid_df) == 2
        assert all((valid_df['latitude'] >= -90) & (valid_df['latitude'] <= 90))
        assert all((valid_df['longitude'] >= -180) & (valid_df['longitude'] <= 180))