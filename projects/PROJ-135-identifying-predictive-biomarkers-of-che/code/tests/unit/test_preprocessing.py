"""
Unit tests for preprocessing functions (T016).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.preprocessing import filter_low_expression_genes, apply_vst_transformation


class TestFilterLowExpressionGenes:
    """Tests for low-expression gene filtering."""

    def test_filter_logic(self):
        """Test that genes with low CPM in most samples are removed."""
        # Create a DataFrame: 5 genes, 10 samples
        # Gene 1: High counts in all samples -> Keep
        # Gene 2: Low counts in 9/10 samples -> Remove
        # Gene 3: Medium counts in 5/10 samples -> Remove (50% < 20% threshold for keeping)
        # Gene 4: Low counts in 2/10 samples -> Keep (80% >= 20% threshold)
        # Gene 5: All zeros -> Remove
        
        np.random.seed(42)
        counts = pd.DataFrame(
            {
                f"sample_{i}": [1000, 10, 5, 100, 0] for i in range(10)
            },
            index=[f"gene_{j}" for j in range(5)]
        )
        # Adjust Gene 4 to have some expression in 8 samples
        counts.loc["gene_3", counts.columns[:8]] = 50
        counts.loc["gene_3", counts.columns[8:]] = 1  # Low in 2 samples

        # Filter with threshold CPM=1, max 80% samples below (i.e., keep if >= 20% samples have CPM>=1)
        filtered = filter_low_expression_genes(counts, cpm_threshold=1.0, sample_fraction=0.8)
        
        # Expected: Gene 0 (high), Gene 3 (medium in 8) should be kept
        # Gene 1 (low in 9), Gene 2 (low in 5), Gene 4 (all 0) should be removed
        assert filtered.shape[0] == 2
        assert "gene_0" in filtered.index
        assert "gene_3" in filtered.index

    def test_no_genes_removed(self):
        """Test case where all genes pass the filter."""
        counts = pd.DataFrame(
            np.random.poisson(100, size=(5, 10)),
            index=[f"gene_{i}" for i in range(5)],
            columns=[f"sample_{j}" for j in range(10)]
        )
        filtered = filter_low_expression_genes(counts, cpm_threshold=1.0, sample_fraction=0.8)
        assert filtered.shape == counts.shape

    def test_all_genes_removed(self):
        """Test case where all genes are removed."""
        counts = pd.DataFrame(
            np.zeros((5, 10)),
            index=[f"gene_{i}" for i in range(5)],
            columns=[f"sample_{j}" for j in range(10)]
        )
        filtered = filter_low_expression_genes(counts, cpm_threshold=1.0, sample_fraction=0.8)
        assert filtered.shape[0] == 0


class TestVSTTransformation:
    """Tests for VST transformation."""

    def test_vst_output_shape(self):
        """Test that VST preserves dimensions."""
        # Create a small count matrix
        np.random.seed(42)
        counts = pd.DataFrame(
            np.random.poisson(50, size=(3, 5)),
            index=[f"gene_{i}" for i in range(3)],
            columns=[f"sample_{j}" for j in range(5)]
        )
        
        # Apply VST
        vst_df = apply_vst_transformation(counts)
        
        # Check shape
        assert vst_df.shape == counts.shape

    def test_vst_values_range(self):
        """Test that VST values are in a reasonable range."""
        np.random.seed(42)
        counts = pd.DataFrame(
            np.random.poisson(100, size=(5, 10)),
            index=[f"gene_{i}" for i in range(5)],
            columns=[f"sample_{j}" for j in range(10)]
        )
        
        vst_df = apply_vst_transformation(counts)
        
        # VST values are typically in a range like -2 to 10 for RNA-seq
        # Just check they are numeric and finite
        assert vst_df.notna().all().all()
        assert np.isfinite(vst_df).all().all()

    def test_vst_with_low_counts(self):
        """Test VST with low counts (edge case)."""
        counts = pd.DataFrame(
            np.random.poisson(1, size=(3, 5)),
            index=[f"gene_{i}" for i in range(3)],
            columns=[f"sample_{j}" for j in range(5)]
        )
        
        vst_df = apply_vst_transformation(counts)
        assert vst_df.shape == counts.shape
        assert np.isfinite(vst_df).all().all()
