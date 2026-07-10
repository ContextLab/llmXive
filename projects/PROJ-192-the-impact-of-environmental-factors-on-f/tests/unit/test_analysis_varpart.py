import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from src.pipelines.analysis import run_variance_partitioning

def test_variance_partitioning_structure():
    """Test that variance partitioning produces correct output structure."""
    # Create dummy data
    with tempfile.TemporaryDirectory() as tmpdir:
        asv_path = os.path.join(tmpdir, "asv_table.tsv")
        meta_path = os.path.join(tmpdir, "metadata.csv")
        out_path = os.path.join(tmpdir, "varpart.csv")
        
        # ASV Table (Samples x Features)
        asv_data = {
            'ASV1': [10, 20, 5, 15],
            'ASV2': [5, 10, 2, 8],
            'ASV3': [0, 5, 1, 3]
        }
        asv_df = pd.DataFrame(asv_data, index=['S1', 'S2', 'S3', 'S4'])
        asv_df.to_csv(asv_path, sep='\t')
        
        # Metadata
        meta_data = {
            'pH': [5.5, 6.0, 5.8, 6.2],
            'nutrients': [100, 150, 120, 160],
            'moisture': [20, 25, 22, 26]
        }
        meta_df = pd.DataFrame(meta_data, index=['S1', 'S2', 'S3', 'S4'])
        meta_df.to_csv(meta_path)
        
        # Run function
        result = run_variance_partitioning(asv_path, meta_path, ['pH', 'nutrients'], out_path)
        
        # Check output file exists
        assert os.path.exists(out_path)
        
        # Check result dataframe structure
        assert 'source' in result.columns
        assert 'variance_component' in result.columns
        assert 'r2' in result.columns
        
        # Check that we have Unique, Shared, Unexplained components
        components = result['variance_component'].tolist()
        assert 'Unique' in components
        assert 'Shared' in components
        assert 'Unexplained' in components
        
        # Check R2 values are between 0 and 1 (approximately, due to floating point)
        assert all((result['r2'] >= 0) & (result['r2'] <= 1.1))

def test_variance_partitioning_single_var():
    """Test variance partitioning with a single variable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        asv_path = os.path.join(tmpdir, "asv_table.tsv")
        meta_path = os.path.join(tmpdir, "metadata.csv")
        out_path = os.path.join(tmpdir, "varpart.csv")
        
        asv_data = {'ASV1': [10, 20, 5, 15], 'ASV2': [5, 10, 2, 8]}
        asv_df = pd.DataFrame(asv_data, index=['S1', 'S2', 'S3', 'S4'])
        asv_df.to_csv(asv_path, sep='\t')
        
        meta_data = {'pH': [5.5, 6.0, 5.8, 6.2]}
        meta_df = pd.DataFrame(meta_data, index=['S1', 'S2', 'S3', 'S4'])
        meta_df.to_csv(meta_path)
        
        result = run_variance_partitioning(asv_path, meta_path, ['pH'], out_path)
        
        assert os.path.exists(out_path)
        assert len(result) == 3 # Unique, Shared (0), Unexplained