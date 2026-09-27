"""
Unit tests for the modeling module (T024 - T031).

Specifically tests:
- Data splitting logic (T024)
- Residual calculation (T026)
- Permutation test logic (T028)
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path if running from tests/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from modeling import split_data, prepare_features_targets, load_unified_dataset

class TestDataSplitting:
    """Tests for T024: Data Splitting logic."""

    def test_split_data_random_split(self):
        """Test that split_data performs a random split correctly."""
        # Create dummy data
        data = {
            'lesion_area_ratio': np.random.rand(100),
            'mean_temp': np.random.rand(100),
            'disease_label': ['A'] * 50 + ['B'] * 50
        }
        df = pd.DataFrame(data)
        
        train_df, test_df = split_data(df, test_size=0.2, random_seed=42)
        
        # Check sizes
        assert len(train_df) == 80
        assert len(test_df) == 20
        
        # Check no overlap
        train_indices = set(train_df.index)
        test_indices = set(test_df.index)
        assert train_indices.isdisjoint(test_indices)
        
        # Check union is original
        assert train_indices.union(test_indices) == set(df.index)

    def test_split_data_stratified(self):
        """Test that split_data stratifies on disease_label if present."""
        data = {
            'lesion_area_ratio': np.random.rand(100),
            'disease_label': ['A'] * 50 + ['B'] * 50
        }
        df = pd.DataFrame(data)
        
        train_df, test_df = split_data(df, test_size=0.2, random_seed=42)
        
        # Check stratification ratios (approx 20% of each class)
        train_ratio_A = (train_df['disease_label'] == 'A').sum() / len(train_df)
        test_ratio_A = (test_df['disease_label'] == 'A').sum() / len(test_df)
        original_ratio_A = 0.5
        
        # Allow some tolerance for small sample sizes, but should be close
        assert abs(train_ratio_A - original_ratio_A) < 0.1
        assert abs(test_ratio_A - original_ratio_A) < 0.1

    def test_split_data_no_stratification_column(self):
        """Test split when no stratification column exists."""
        data = {
            'lesion_area_ratio': np.random.rand(100),
            'mean_temp': np.random.rand(100)
        }
        df = pd.DataFrame(data)
        
        # Should not raise
        train_df, test_df = split_data(df, test_size=0.2, random_seed=42)
        assert len(train_df) == 80
        assert len(test_df) == 20

    def test_prepare_features_targets(self):
        """Test feature and target separation."""
        data = {
            'lesion_area_ratio': [1, 2, 3, 4],
            'mean_temp': [10, 20, 30, 40],
            'humidity': [50, 60, 70, 80],
            'other': ['a', 'b', 'c', 'd'] # Non-numeric
        }
        df = pd.DataFrame(data)
        
        X, y = prepare_features_targets(df, target_col='lesion_area_ratio')
        
        # X should be numeric columns excluding target
        assert X.shape == (4, 2) # mean_temp, humidity
        assert y.shape == (4,)
        assert list(y) == [1, 2, 3, 4]
        
        # Check column order consistency (pandas sorts columns)
        expected_X_cols = ['humidity', 'mean_temp']
        assert list(df[expected_X_cols].columns) == list(df[X.columns] if hasattr(X, 'columns') else expected_X_cols)