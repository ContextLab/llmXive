"""
Unit tests for VST preprocessing functions.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import tempfile
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.preprocessing import filter_low_expression_genes, load_processed_data, save_processed_data

class TestFilterLowExpressionGenes:
    """Test cases for low-expression gene filtering."""
    
    def test_filter_keeps_high_expression_genes(self):
        """Test that genes with high CPM are kept."""
        # Create a DataFrame with some high and low expression genes
        np.random.seed(42)
        n_genes = 100
        n_samples = 10
        
        # Create counts matrix
        counts = np.random.poisson(100, size=(n_genes, n_samples))
        
        # Make some genes low expression (very low counts)
        counts[80:, :] = np.random.poisson(1, size=(20, n_samples))
        
        df = pd.DataFrame(
            counts,
            index=[f"Gene_{i}" for i in range(n_genes)],
            columns=[f"Sample_{i}" for i in range(n_samples)]
        )
        
        # Filter
        filtered_df, removed_count = filter_low_expression_genes(df)
        
        # Check that low expression genes were removed
        assert removed_count > 0, "Some low expression genes should be removed"
        assert filtered_df.shape[0] < n_genes, "Some genes should be filtered out"
        assert filtered_df.shape[1] == n_samples, "Number of samples should remain the same"
        
    def test_filter_with_all_high_expression(self):
        """Test filtering when all genes have high expression."""
        np.random.seed(42)
        n_genes = 50
        n_samples = 20
        
        # All genes have high counts
        counts = np.random.poisson(100, size=(n_genes, n_samples))
        
        df = pd.DataFrame(
            counts,
            index=[f"Gene_{i}" for i in range(n_genes)],
            columns=[f"Sample_{i}" for i in range(n_samples)]
        )
        
        filtered_df, removed_count = filter_low_expression_genes(df)
        
        # Very few or no genes should be removed
        assert removed_count <= 5, "Few or no genes should be removed when all are high expression"
        assert filtered_df.shape[0] >= n_genes - 5
        
    def test_filter_with_all_low_expression(self):
        """Test filtering when all genes have low expression."""
        np.random.seed(42)
        n_genes = 50
        n_samples = 20
        
        # All genes have very low counts
        counts = np.random.poisson(1, size=(n_genes, n_samples))
        
        df = pd.DataFrame(
            counts,
            index=[f"Gene_{i}" for i in range(n_genes)],
            columns=[f"Sample_{i}" for i in range(n_samples)]
        )
        
        # This should raise an error because all genes would be filtered
        with pytest.raises(ValueError, match="All genes were filtered out"):
            filter_low_expression_genes(df)
            
    def test_filter_threshold_logic(self):
        """Test that the threshold logic works correctly."""
        # Create a specific case: 10 samples, threshold is 80%
        # So we need CPM >= 1 in at least 2 samples (20%) to keep a gene
        n_samples = 10
        min_samples_to_keep = 2  # 20% of 10
        
        # Create a gene that has CPM >= 1 in exactly 1 sample (should be removed)
        # and another that has CPM >= 1 in 2 samples (should be kept)
        
        # Library sizes are all 1e6 for simplicity
        counts = np.zeros((2, n_samples), dtype=int)
        
        # Gene 0: CPM >= 1 in only 1 sample
        counts[0, 0] = 1000  # CPM = 1 (with lib size 1e6)
        
        # Gene 1: CPM >= 1 in 2 samples
        counts[1, 0] = 1000
        counts[1, 1] = 1000
        
        df = pd.DataFrame(
            counts,
            index=["Gene_0", "Gene_1"],
            columns=[f"Sample_{i}" for i in range(n_samples)]
        )
        
        filtered_df, removed_count = filter_low_expression_genes(df)
        
        # Gene 0 should be removed, Gene 1 should be kept
        assert filtered_df.shape[0] == 1
        assert "Gene_1" in filtered_df.index
        assert "Gene_0" not in filtered_df.index

class TestLoadSaveProcessedData:
    """Test cases for loading and saving processed data."""
    
    def test_save_and_load_processed_data(self, tmp_path):
        """Test that data can be saved and loaded correctly."""
        # Create test data
        np.random.seed(42)
        data = np.random.rand(50, 20)
        df = pd.DataFrame(
            data,
            index=[f"Gene_{i}" for i in range(50)],
            columns=[f"Sample_{i}" for i in range(20)]
        )
        
        # Save
        output_path = tmp_path / "test_data.csv"
        save_processed_data(df, str(output_path))
        
        # Load
        loaded_df = load_processed_data(str(output_path))
        
        # Check
        assert loaded_df.shape == df.shape
        assert list(loaded_df.index) == list(df.index)
        assert list(loaded_df.columns) == list(df.columns)
        np.testing.assert_array_almost_equal(loaded_df.values, df.values)
        
    def test_load_nonexistent_file(self, tmp_path):
        """Test that loading a nonexistent file raises an error."""
        with pytest.raises(FileNotFoundError):
            load_processed_data(str(tmp_path / "nonexistent.csv"))
            
    def test_load_empty_file(self, tmp_path):
        """Test that loading an empty file raises an error."""
        empty_path = tmp_path / "empty.csv"
        empty_path.touch()
        
        with pytest.raises(ValueError, match="Loaded data"):
            load_processed_data(str(empty_path))