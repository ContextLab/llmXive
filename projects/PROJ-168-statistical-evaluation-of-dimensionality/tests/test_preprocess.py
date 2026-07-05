"""
Tests for the preprocessing module.
"""
import os
import sys
import tempfile
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
from scipy import sparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.preprocess import (
    _filter_genes_by_expression,
    _select_hvgs,
    _sample_cells_deterministic,
    preprocess_accession,
    GENE_FILTER_THRESHOLD,
    MAX_CELLS,
    DEFAULT_N_HVGS
)

class TestPreprocessFunctions(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple test matrix: 10 genes x 20 cells
        np.random.seed(42)
        data = np.random.poisson(2, (10, 20))
        # Make some genes very sparse
        data[0, :] = 0  # Gene 0: all zeros
        data[1, :] = 0
        data[1, :5] = [1, 1, 1, 1, 1]  # Gene 1: 5/20 = 25% (passes 5%)
        data[2, :1] = [1]  # Gene 2: 1/20 = 5% (passes 5%)
        data[3, :0] = []  # Gene 3: 0/20 = 0% (fails 5%)
        
        self.sparse_matrix = sparse.csr_matrix(data)
        self.dense_matrix = data
        self.accession = "TEST123"
    
    def test_filter_genes_by_expression_sparse(self):
        """Test gene filtering on sparse matrix."""
        filtered_matrix, mask = _filter_genes_by_expression(self.sparse_matrix, 0.05)
        
        # Gene 0, 3 should be filtered out (0% and 0% expression)
        # Gene 1 (25%), Gene 2 (5%) should remain
        # Note: Gene 2 is exactly 5%, which passes >= 5%
        expected_mask = [False, True, True, False] + [True] * 6  # Remaining genes have >0
        
        # Check that we removed the all-zero rows
        self.assertEqual(filtered_matrix.shape[0], 8)  # 10 - 2 removed
        self.assertTrue(np.all(mask == expected_mask[:10]))
    
    def test_filter_genes_by_expression_dense(self):
        """Test gene filtering on dense matrix."""
        filtered_matrix, mask = _filter_genes_by_expression(self.dense_matrix, 0.05)
        
        # Same logic as sparse
        self.assertEqual(filtered_matrix.shape[0], 8)
    
    def test_select_hvgs(self):
        """Test HVG selection."""
        # Create a matrix with known variance structure
        np.random.seed(123)
        matrix = np.random.poisson(2, (100, 50))
        # Make gene 0 have very high variance
        matrix[0, :] = np.random.poisson(10, 50)
        sparse_matrix = sparse.csr_matrix(matrix)
        
        filtered_matrix, mask = _select_hvgs(sparse_matrix, n_top_genes=5, accession="TEST")
        
        # Should select 5 genes
        self.assertEqual(filtered_matrix.shape[0], 5)
        self.assertEqual(np.sum(mask), 5)
    
    def test_sample_cells_deterministic(self):
        """Test deterministic cell sampling."""
        # Create a matrix with 15000 cells (exceeds MAX_CELLS)
        np.random.seed(456)
        matrix = np.random.poisson(2, (100, 15000))
        sparse_matrix = sparse.csr_matrix(matrix)
        
        sampled_matrix, indices = _sample_cells_deterministic(
            sparse_matrix, 
            accession="DETERMINISTIC_TEST", 
            max_cells=10000
        )
        
        # Check dimensions
        self.assertEqual(sampled_matrix.shape[1], 10000)
        self.assertEqual(len(indices), 10000)
        
        # Check determinism: run again with same accession
        sampled_matrix2, indices2 = _sample_cells_deterministic(
            sparse_matrix, 
            accession="DETERMINISTIC_TEST", 
            max_cells=10000
        )
        
        # Indices should be identical
        self.assertEqual(indices, indices2)
    
    def test_sample_cells_no_sampling_needed(self):
        """Test that no sampling occurs when cell count is low."""
        matrix = np.random.poisson(2, (100, 5000))
        sparse_matrix = sparse.csr_matrix(matrix)
        
        sampled_matrix, indices = _sample_cells_deterministic(
            sparse_matrix, 
            accession="LOW_CELL_TEST", 
            max_cells=10000
        )
        
        # Should return original matrix
        self.assertEqual(sampled_matrix.shape[1], 5000)
        self.assertEqual(indices, list(range(5000)))

class TestPreprocessAccession(unittest.TestCase):
    
    def test_full_pipeline(self):
        """Test the full preprocessing pipeline."""
        # Create a temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Create a simple gene x cell matrix
            np.random.seed(789)
            data = np.random.poisson(3, (50, 12000))  # 50 genes, 12000 cells
            # Add some structure
            data[0, :] = 0  # All zeros
            data[1, :5] = [1, 1, 1, 1, 1]  # Low expression
            
            df = pd.DataFrame(
                data,
                index=[f"Gene_{i}" for i in range(50)],
                columns=[f"Cell_{i}" for i in range(12000)]
            )
            df.to_csv(f.name)
            input_path = f.name
        
        # Create temporary output path
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as out_f:
            output_path = out_f.name
        
        try:
            # Run preprocessing
            stats = preprocess_accession(
                input_path=input_path,
                output_path=output_path,
                accession="FULL_PIPELINE_TEST",
                n_top_genes=10,
                gene_threshold=0.05,
                max_cells=10000
            )
            
            # Check stats
            self.assertEqual(stats["accession"], "FULL_PIPELINE_TEST")
            self.assertEqual(stats["initial_cells"], 12000)
            self.assertEqual(stats["final_cells"], 10000)  # Sampled down
            self.assertTrue(stats["sampled"])
            
            # Check output file exists and is valid
            self.assertTrue(os.path.exists(output_path))
            output_df = pd.read_csv(output_path, index_col=0)
            self.assertEqual(output_df.shape[1], 10000)
            self.assertLessEqual(output_df.shape[0], 10)  # HVGs selected
            
            # Check metadata file
            metadata_path = output_path.replace('.csv', '_metadata.json')
            self.assertTrue(os.path.exists(metadata_path))
            with open(metadata_path, 'r') as mf:
                meta = json.load(mf)
            self.assertEqual(meta["accession"], "FULL_PIPELINE_TEST")
            
        finally:
            # Cleanup
            if os.path.exists(input_path):
                os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
            metadata_path = output_path.replace('.csv', '_metadata.json')
            if os.path.exists(metadata_path):
                os.unlink(metadata_path)

if __name__ == "__main__":
    unittest.main()