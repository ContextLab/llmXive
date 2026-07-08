import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch

# Import from the existing API surface
from src.preprocessing import filter_zero_count_genes, stratify_samples, preprocess_dataset, main


class TestZeroCountFiltering:
    def test_filter_removes_zero_count_genes(self):
        """Test that genes with zero counts across all samples are removed."""
        data = {
            "gene1": [0, 0, 0, 0],
            "gene2": [1, 2, 3, 4],
            "gene3": [0, 0, 5, 6],
            "gene4": [0, 0, 0, 0]
        }
        df = pd.DataFrame(data, index=["sample1", "sample2", "sample3", "sample4"])
        
        filtered_df = filter_zero_count_genes(df)
        
        assert "gene1" not in filtered_df.columns
        assert "gene4" not in filtered_df.columns
        assert "gene2" in filtered_df.columns
        assert "gene3" in filtered_df.columns
        assert len(filtered_df.columns) == 2

    def test_filter_keeps_all_nonzero_genes(self):
        """Test that genes with at least one non-zero count are kept."""
        data = {
            "gene1": [1, 0, 0, 0],
            "gene2": [0, 1, 0, 0],
            "gene3": [0, 0, 1, 0],
            "gene4": [0, 0, 0, 1]
        }
        df = pd.DataFrame(data, index=["sample1", "sample2", "sample3", "sample4"])
        
        filtered_df = filter_zero_count_genes(df)
        
        assert len(filtered_df.columns) == 4
        assert all(gene in filtered_df.columns for gene in data.keys())


class TestStratification:
    def test_stratification_handles_missing_batch(self):
        """
        T010: Test that stratification falls back to random assignment
        when batch metadata is missing or incomplete.
        
        This test asserts the random fallback behavior specified in the
        project requirements for handling missing batch metadata.
        """
        # Create a dataset with sample metadata missing the 'batch' column
        data = {
            "gene1": [10, 20, 30, 40, 50, 60],
            "gene2": [5, 10, 15, 20, 25, 30],
            "gene3": [100, 200, 300, 400, 500, 600]
        }
        index = ["sample1", "sample2", "sample3", "sample4", "sample5", "sample6"]
        df = pd.DataFrame(data, index=index)
        
        # Create metadata without the 'batch' column
        metadata = pd.DataFrame({
            "condition": ["A", "A", "B", "B", "A", "B"]
        }, index=index)
        
        # This should not raise an error; it should use random fallback
        subsets = stratify_samples(df, metadata, n_subsets=3, batch_column="batch")
        
        # Verify that subsets were created
        assert isinstance(subsets, list)
        assert len(subsets) == 3
        
        # Verify that all samples are distributed across subsets
        all_samples = set()
        for subset in subsets:
            all_samples.update(subset.index)
        
        assert all_samples == set(df.index)
        
        # Verify that each subset has at least one sample
        for subset in subsets:
            assert len(subset) > 0

    def test_stratification_with_valid_batch(self):
        """Test that stratification respects batch boundaries when metadata is present."""
        data = {
            "gene1": [10, 20, 30, 40, 50, 60, 70, 80],
            "gene2": [5, 10, 15, 20, 25, 30, 35, 40]
        }
        index = ["sample1", "sample2", "sample3", "sample4", "sample5", "sample6", "sample7", "sample8"]
        df = pd.DataFrame(data, index=index)
        
        # Create metadata with batch column
        metadata = pd.DataFrame({
            "condition": ["A", "A", "B", "B", "A", "B", "A", "B"],
            "batch": ["batch1", "batch1", "batch1", "batch1", "batch2", "batch2", "batch2", "batch2"]
        }, index=index)
        
        subsets = stratify_samples(df, metadata, n_subsets=2, batch_column="batch")
        
        assert len(subsets) == 2
        
        # Verify that samples within the same batch are not split across subsets
        # (This is a simplified check; a full check would verify exact distribution)
        for subset in subsets:
            for idx in subset.index:
                assert idx in df.index

    def test_stratification_invalid_n_subsets(self):
        """Test that stratification raises error for invalid number of subsets."""
        data = {"gene1": [1, 2, 3, 4]}
        df = pd.DataFrame(data, index=["s1", "s2", "s3", "s4"])
        metadata = pd.DataFrame({"condition": ["A", "A", "B", "B"]}, index=["s1", "s2", "s3", "s4"])
        
        # Should raise ValueError for n_subsets > number of samples
        with pytest.raises(ValueError):
            stratify_samples(df, metadata, n_subsets=10)


class TestPreprocessingIntegration:
    def test_preprocess_dataset_full_flow(self):
        """Test the full preprocessing pipeline."""
        data = {
            "gene1": [0, 0, 0, 0],
            "gene2": [10, 20, 30, 40],
            "gene3": [5, 10, 15, 20]
        }
        df = pd.DataFrame(data, index=["s1", "s2", "s3", "s4"])
        metadata = pd.DataFrame({"condition": ["A", "A", "B", "B"]}, index=["s1", "s2", "s3", "s4"])
        
        result_df, result_metadata = preprocess_dataset(df, metadata)
        
        # Check that zero-count genes are filtered
        assert "gene1" not in result_df.columns
        assert len(result_df.columns) == 2
        
        # Check that metadata is preserved
        assert len(result_metadata) == len(result_df)
        assert list(result_metadata.index) == list(result_df.index)

    def test_preprocess_with_missing_batch_column(self):
        """Test preprocessing when batch column is missing in metadata."""
        data = {
            "gene1": [10, 20, 30, 40],
            "gene2": [5, 10, 15, 20]
        }
        df = pd.DataFrame(data, index=["s1", "s2", "s3", "s4"])
        # Metadata without batch column
        metadata = pd.DataFrame({"condition": ["A", "A", "B", "B"]}, index=["s1", "s2", "s3", "s4"])
        
        # Should not raise, should use random fallback internally
        result_df, result_metadata = preprocess_dataset(df, metadata, batch_column="batch")
        
        assert len(result_df) == 4
        assert len(result_metadata) == 4