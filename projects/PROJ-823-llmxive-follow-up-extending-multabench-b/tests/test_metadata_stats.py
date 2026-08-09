"""
Unit tests for metadata statistics computation.
"""
import os
import sys
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from analysis.metadata_stats import (
    compute_feature_stats,
    compute_cardinality_for_dataset,
    compute_missingness_for_dataset,
    compute_sparsity_for_dataset,
    compute_variance_for_dataset
)

class TestFeatureStats:
    def test_compute_feature_stats_basic(self):
        """Test basic feature statistics computation."""
        data = {
            'col1': [1.0, 2.0, 3.0, 4.0, 5.0],
            'col2': [1.0, np.nan, 3.0, 4.0, 5.0],
            'col3': [0.0, 0.0, 1.0, 0.0, 2.0]
        }
        df = pd.DataFrame(data)
        numeric_cols = ['col1', 'col2', 'col3']
        
        stats = compute_feature_stats(df, numeric_cols)
        
        # Check col1 (no missing, no zeros)
        assert stats['col1']['missingness'] == 0.0
        assert stats['col1']['sparsity'] == 0.0
        assert stats['col1']['variance'] > 0
        
        # Check col2 (1 missing out of 5)
        assert abs(stats['col2']['missingness'] - 0.2) < 1e-6
        
        # Check col3 (sparsity)
        assert stats['col3']['sparsity'] > 0  # 3 zeros out of 5
    
    def test_compute_feature_stats_empty_df(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame()
        stats = compute_feature_stats(df, [])
        assert stats == {}

class TestCardinality:
    def test_compute_cardinality_categorical(self):
        """Test cardinality with categorical data."""
        data = {
            'cat_col': ['A', 'B', 'A', 'C', 'B', 'A'],
            'num_col': [1, 2, 3, 4, 5, 6]
        }
        df = pd.DataFrame(data)
        
        result = compute_cardinality_for_dataset("test_ds", df)
        
        assert result['dataset_id'] == "test_ds"
        assert result['cardinality'] > 0
    
    def test_compute_cardinality_all_unique(self):
        """Test cardinality when all values are unique."""
        data = {
            'col1': list(range(100)),
            'col2': list(range(100, 200))
        }
        df = pd.DataFrame(data)
        
        result = compute_cardinality_for_dataset("unique_ds", df)
        
        # Both columns have 100 unique values, mean should be 100
        assert result['cardinality'] == 100.0

class TestMissingness:
    def test_compute_missingness_with_nan(self):
        """Test missingness calculation with NaN values."""
        data = {
            'col1': [1.0, np.nan, 3.0, np.nan, 5.0],
            'col2': [1.0, 2.0, 3.0, 4.0, 5.0]
        }
        df = pd.DataFrame(data)
        
        result = compute_missingness_for_dataset("missing_ds", df)
        
        # col1: 2/5 missing, col2: 0/5 missing -> mean = 0.2
        assert abs(result['missingness'] - 0.2) < 1e-6

class TestSparsity:
    def test_compute_sparsity_with_zeros(self):
        """Test sparsity calculation with zero values."""
        data = {
            'col1': [0.0, 0.0, 1.0, 0.0, 2.0],
            'col2': [1.0, 2.0, 3.0, 4.0, 5.0]
        }
        df = pd.DataFrame(data)
        
        result = compute_sparsity_for_dataset("sparse_ds", df)
        
        # col1: 3 zeros out of 5 non-missing = 0.6
        # col2: 0 zeros out of 5 = 0.0
        # mean = 0.3
        assert abs(result['sparsity'] - 0.3) < 1e-6

class TestVariance:
    def test_compute_variance_constant(self):
        """Test variance with constant values (should be 0)."""
        data = {
            'col1': [5.0, 5.0, 5.0, 5.0],
            'col2': [1.0, 2.0, 3.0, 4.0]
        }
        df = pd.DataFrame(data)
        
        result = compute_variance_for_dataset("const_ds", df)
        
        # col1 variance = 0, col2 variance > 0
        # mean > 0
        assert result['variance'] > 0
    
    def test_compute_variance_single_value(self):
        """Test variance with single value (should be 0 or NaN handled)."""
        data = {
            'col1': [5.0]
        }
        df = pd.DataFrame(data)
        
        result = compute_variance_for_dataset("single_ds", df)
        
        # With single value, variance is 0 (handled in compute_feature_stats)
        assert result['variance'] == 0.0
    
    def test_compute_variance_no_numeric(self):
        """Test variance with no numeric columns."""
        data = {
            'cat1': ['A', 'B', 'C'],
            'cat2': ['X', 'Y', 'Z']
        }
        df = pd.DataFrame(data)
        
        result = compute_variance_for_dataset("no_num_ds", df)
        
        assert result['dataset_id'] == "no_num_ds"
        assert result['variance'] == 0.0

class TestIntegration:
    def test_all_stats_consistency(self):
        """Test that all stats functions work on same dataset."""
        data = {
            'num1': [1.0, 2.0, np.nan, 4.0, 0.0],
            'num2': [10.0, 20.0, 30.0, 40.0, 50.0],
            'cat1': ['A', 'B', 'A', 'C', 'B']
        }
        df = pd.DataFrame(data)
        
        # All should return valid results
        card = compute_cardinality_for_dataset("test", df)
        miss = compute_missingness_for_dataset("test", df)
        spar = compute_sparsity_for_dataset("test", df)
        var = compute_variance_for_dataset("test", df)
        
        assert 'dataset_id' in card
        assert 'cardinality' in card
        assert 'missingness' in miss
        assert 'sparsity' in spar
        assert 'variance' in var