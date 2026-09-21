"""
Unit tests for T043: Performance Optimization
"""
import os
import tempfile
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

# Import the optimization functions
from analysis.optimization_pipeline import (
    optimize_dataframe_dtypes,
    optimize_centrality_data,
    optimize_behavioral_data
)

class TestDtypeOptimization:
    def test_float64_to_float32(self):
        """Test that float64 columns are downcast to float32."""
        df = pd.DataFrame({
            'col1': [1.0, 2.0, 3.0],
            'col2': [10.0, 20.0, 30.0]
        })
        # Force float64
        df['col1'] = df['col1'].astype(np.float64)
        df['col2'] = df['col2'].astype(np.float64)
        
        assert df['col1'].dtype == np.float64
        
        optimized_df = optimize_dataframe_dtypes(df)
        
        # Check if downcast occurred (within float32 range)
        assert optimized_df['col1'].dtype == np.float32
        assert optimized_df['col2'].dtype == np.float32

    def test_string_preservation(self):
        """Test that string columns are not modified."""
        df = pd.DataFrame({
            'id': ['A', 'B', 'C'],
            'val': [1.0, 2.0, 3.0]
        })
        
        optimized_df = optimize_dataframe_dtypes(df)
        
        assert optimized_df['id'].dtype == object
        assert optimized_df['val'].dtype == np.float32

    def test_memory_reduction(self):
        """Test that memory usage is reduced."""
        # Create a large dataframe
        n_rows = 10000
        df = pd.DataFrame({
            'val1': np.random.rand(n_rows).astype(np.float64),
            'val2': np.random.rand(n_rows).astype(np.float64),
            'val3': np.random.rand(n_rows).astype(np.float64)
        })
        
        initial_mem = df.memory_usage(deep=True).sum()
        optimized_df = optimize_dataframe_dtypes(df)
        final_mem = optimized_df.memory_usage(deep=True).sum()
        
        assert final_mem < initial_mem
        assert optimized_df['val1'].dtype == np.float32

class TestFileOptimization:
    def test_optimize_centrality_data(self):
        """Test optimization of centrality CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.csv')
            output_path = os.path.join(tmpdir, 'output.csv')
            
            # Create dummy data
            df = pd.DataFrame({
                'subject_id': ['S1', 'S2'],
                'region_id': [1, 2],
                'region_name': ['A', 'B'],
                'degree': [10.0, 20.0],
                'betweenness': [0.5, 0.8],
                'eigenvector': [0.1, 0.2]
            })
            df.to_csv(input_path, index=False)
            
            optimize_centrality_data(input_path, output_path)
            
            assert os.path.exists(output_path)
            result_df = pd.read_csv(output_path)
            
            assert 'degree' in result_df.columns
            assert result_df['degree'].dtype == np.float32

    def test_optimize_behavioral_data(self):
        """Test optimization of behavioral CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.csv')
            output_path = os.path.join(tmpdir, 'output.csv')
            
            # Create dummy data
            df = pd.DataFrame({
                'subject_id': ['S1', 'S2'],
                'pre_motor_score': [50.0, 60.0],
                'post_motor_score': [70.0, 80.0],
                'age': [25.0, 30.0],
                'sex': ['M', 'F'],
                'improvement_score': [20.0, 20.0]
            })
            df.to_csv(input_path, index=False)
            
            optimize_behavioral_data(input_path, output_path)
            
            assert os.path.exists(output_path)
            result_df = pd.read_csv(output_path)
            
            assert result_df['improvement_score'].dtype == np.float32
            assert result_df['age'].dtype == np.float32