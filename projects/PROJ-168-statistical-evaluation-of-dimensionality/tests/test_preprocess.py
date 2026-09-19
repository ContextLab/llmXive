"""
tests/test_preprocess.py

Unit tests for the preprocess.py module.
These tests verify HVG selection, gene filtering, and deterministic sampling.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from preprocess import (
    PreprocessingError,
    load_count_matrix,
    filter_low_expr_genes,
    calculate_variance_stabilized_variance,
    detect_elbow_knee,
    select_hvgs,
    deterministic_sample_cells
)

class TestPreprocessing(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures with synthetic count data."""
        np.random.seed(42)
        n_cells = 500
        n_genes = 1000
        
        # Create synthetic count matrix (Poisson-like distribution)
        self.counts = np.random.poisson(lam=5, size=(n_cells, n_genes)).astype(float)
        
        # Create gene names
        self.gene_names = [f"GENE_{i:04d}" for i in range(n_genes)]
        self.cell_names = [f"CELL_{i:04d}" for i in range(n_cells)]
        
        # Create DataFrame
        self.df = pd.DataFrame(
            self.counts,
            index=self.cell_names,
            columns=self.gene_names
        )

    def test_filter_low_expr_genes(self):
        """Test filtering of genes expressed in less than 5% of cells."""
        # Create data where some genes are expressed in very few cells
        df_test = self.df.copy()
        # Make first 100 genes expressed in only 1 cell (0.2%)
        df_test.iloc[:, :100] = 0
        df_test.iloc[0, :100] = 10  # Expressed in just first cell
        
        filtered_df = filter_low_expr_genes(df_test, threshold_pct=5.0)
        
        # First 100 genes should be removed
        self.assertNotIn("GENE_0000", filtered_df.columns)
        self.assertNotIn("GENE_0099", filtered_df.columns)
        
        # Remaining genes should be present (assuming they meet threshold)
        self.assertIn("GENE_0100", filtered_df.columns)
        
        # Verify shape
        self.assertLess(len(filtered_df.columns), len(df_test.columns))
        self.assertEqual(len(filtered_df.index), len(df_test.index))

    def test_calculate_variance_stabilized_variance(self):
        """Test VST variance calculation."""
        # Calculate variance for a simple dataset
        series = pd.Series([1, 2, 3, 4, 5, 10, 20, 30])
        
        # This should not raise an error
        vst_var = calculate_variance_stabilized_variance(series)
        
        self.assertIsInstance(vst_var, float)
        self.assertGreaterEqual(vst_var, 0)

    def test_detect_elbow_knee(self):
        """Test elbow detection algorithm."""
        # Create a curve with a clear elbow
        # High variance genes should be at the beginning
        variances = np.array([100, 80, 60, 40, 20, 10, 5, 4, 3, 2, 1.5, 1.2, 1.0])
        
        elbow_idx = detect_elbow_knee(variances)
        
        # Elbow should be detected somewhere in the first half
        self.assertLess(elbow_idx, len(variances) // 2)
        self.assertGreaterEqual(elbow_idx, 0)

    def test_select_hvgs(self):
        """Test HVG selection returns correct number of genes."""
        # Select top 50 HVGs
        hvgs = select_hvgs(self.df, n_hvgs=50)
        
        self.assertEqual(len(hvgs), 50)
        self.assertTrue(all(g in self.df.columns for g in hvgs))
        
        # Verify they are high variance (compare to random selection)
        hvg_vars = []
        for g in hvgs:
            hvg_vars.append(np.var(self.df[g]))
        
        random_genes = np.random.choice(self.df.columns, 50, replace=False)
        random_vars = [np.var(self.df[g]) for g in random_genes]
        
        # HVGs should have higher average variance
        self.assertGreater(np.mean(hvg_vars), np.mean(random_vars))

    def test_deterministic_sample_cells(self):
        """Test that sampling is deterministic based on seed."""
        n_samples = 100
        
        # Sample with same seed twice
        sampled1 = deterministic_sample_cells(self.df, n_samples=n_samples, seed="test_seed")
        sampled2 = deterministic_sample_cells(self.df, n_samples=n_samples, seed="test_seed")
        
        # Should be identical
        self.assertTrue(sampled1.equals(sampled2))
        
        # Sample with different seed
        sampled3 = deterministic_sample_cells(self.df, n_samples=n_samples, seed="different_seed")
        
        # Should be different (with high probability)
        self.assertFalse(sampled1.equals(sampled3))
        
        # Verify sample size
        self.assertEqual(len(sampled1), n_samples)

    def test_deterministic_sample_cells_with_hash(self):
        """Test deterministic sampling using accession hash."""
        n_samples = 50
        accession = "GSE12345"
        
        # Sample twice with same accession
        sampled1 = deterministic_sample_cells(self.df, n_samples=n_samples, seed=accession)
        sampled2 = deterministic_sample_cells(self.df, n_samples=n_samples, seed=accession)
        
        self.assertTrue(sampled1.equals(sampled2))

    def test_filter_low_expr_genes_all_removed(self):
        """Test handling when all genes are filtered out."""
        # Create data where all genes are expressed in < 1% of cells
        df_sparse = pd.DataFrame(np.zeros((100, 50)))
        df_sparse.iloc[0, 0] = 1  # Only one non-zero value
        
        with self.assertRaises(PreprocessingError):
            filter_low_expr_genes(df_sparse, threshold_pct=5.0)

    def test_select_hvgs_more_than_available(self):
        """Test HVG selection when requested more than available."""
        n_genes = len(self.df.columns)
        # Request more HVGs than exist
        hvgs = select_hvgs(self.df, n_hvgs=n_genes + 100)
        
        # Should return all available genes
        self.assertEqual(len(hvgs), n_genes)

if __name__ == '__main__':
    unittest.main()
