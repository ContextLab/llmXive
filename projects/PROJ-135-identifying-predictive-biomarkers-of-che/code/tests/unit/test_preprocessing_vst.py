import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.preprocessing import filter_low_expression_genes, load_processed_data

class TestFilterLowExpressionGenes:
    """Unit tests for low-expression gene filtering logic."""

    def test_filter_genes_expressed_in_most_samples(self):
        """Test that genes expressed in most samples are kept."""
        # Create a mock DataFrame
        # 5 samples, 4 genes
        # Gene 0: CPM < 1 in all samples (filter out)
        # Gene 1: CPM >= 1 in 3/5 samples (keep, >= 20%)
        # Gene 2: CPM >= 1 in 1/5 samples (keep, >= 20%)
        # Gene 3: CPM < 1 in 4/5 samples (filter out, < 20% expressed)
        
        expression_data = [
            [10, 100, 5, 2],    # Sample 0: totals = 117
            [15, 120, 3, 1],    # Sample 1: totals = 139
            [8, 90, 2, 0],      # Sample 2: totals = 100
            [12, 110, 4, 1],    # Sample 3: totals = 127
            [20, 130, 6, 0],    # Sample 4: totals = 156
        ]
        
        gene_symbols = ["GeneA", "GeneB", "GeneC", "GeneD"]
        
        df = pd.DataFrame({
            'sample_id': [f'sample_{i}' for i in range(5)],
            'tumor_type': ['BRCA'] * 5,
            'response_label': ['responder'] * 5,
            'gene_symbols': [gene_symbols] * 5,
            'expression_vector': expression_data
        })
        
        # Calculate expected CPM manually for verification
        # Sample 0: totals = 117
        # GeneA: 10/117*1e6 = 85470.94 (>= 1, expressed)
        # GeneB: 100/117*1e6 = 854700.85 (>= 1, expressed)
        # GeneC: 5/117*1e6 = 42735.04 (>= 1, expressed)
        # GeneD: 2/117*1e6 = 17094.02 (>= 1, expressed)
        
        # Actually, all genes have CPM > 1 in all samples with these counts
        # Let's use smaller counts to create low-expression genes
        
        expression_data_low = [
            [1, 100, 5, 0],    # Sample 0: totals = 106
            [1, 120, 3, 0],    # Sample 1: totals = 124
            [1, 90, 2, 0],     # Sample 2: totals = 93
            [1, 110, 4, 0],    # Sample 3: totals = 115
            [1, 130, 6, 0],    # Sample 4: totals = 137
        ]
        
        df = pd.DataFrame({
            'sample_id': [f'sample_{i}' for i in range(5)],
            'tumor_type': ['BRCA'] * 5,
            'response_label': ['responder'] * 5,
            'gene_symbols': [gene_symbols] * 5,
            'expression_vector': expression_data_low
        })
        
        # GeneA: count=1 in all samples
        # CPM for GeneA in each sample:
        # S0: 1/106*1e6 = 9433.96 (>= 1)
        # All samples: >= 1
        # So GeneA is expressed in 5/5 = 100% of samples -> keep
        
        # GeneD: count=0 in all samples
        # CPM = 0 in all samples -> filter out (0% expressed < 20%)
        
        filtered_df, filtered_genes = filter_low_expression_genes(
            df, cpm_threshold=1.0, sample_fraction=0.8
        )
        
        # GeneD should be filtered out
        assert "GeneD" in filtered_genes
        assert len(filtered_genes) == 1
        
        # GeneA, GeneB, GeneC should be kept
        kept_symbols = filtered_df['gene_symbols'].iloc[0]
        assert "GeneA" in kept_symbols
        assert "GeneB" in kept_symbols
        assert "GeneC" in kept_symbols
        assert "GeneD" not in kept_symbols

    def test_filter_genes_expressed_in_few_samples(self):
        """Test that genes expressed in very few samples are filtered out."""
        # Gene expressed in only 1 out of 10 samples (10% < 20%)
        n_samples = 10
        n_genes = 3
        
        expression_data = []
        for i in range(n_samples):
            # Gene 0: high expression in all samples
            # Gene 1: high expression in all samples
            # Gene 2: high expression only in sample 0
            if i == 0:
                row = [100, 100, 100]
            else:
                row = [100, 100, 0]
            expression_data.append(row)
        
        gene_symbols = ["High1", "High2", "Low"]
        
        df = pd.DataFrame({
            'sample_id': [f'sample_{i}' for i in range(n_samples)],
            'tumor_type': ['BRCA'] * n_samples,
            'response_label': ['responder'] * n_samples,
            'gene_symbols': [gene_symbols] * n_samples,
            'expression_vector': expression_data
        })
        
        filtered_df, filtered_genes = filter_low_expression_genes(
            df, cpm_threshold=1.0, sample_fraction=0.8
        )
        
        # "Low" gene is expressed in 1/10 = 10% of samples (< 20%)
        # Should be filtered out
        assert "Low" in filtered_genes
        assert len(filtered_genes) == 1

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame({
            'sample_id': [],
            'tumor_type': [],
            'response_label': [],
            'gene_symbols': [],
            'expression_vector': []
        })
        
        filtered_df, filtered_genes = filter_low_expression_genes(df)
        
        assert filtered_df.empty
        assert filtered_genes == []

    def test_all_genes_filtered(self):
        """Test when all genes should be filtered out."""
        # All genes have 0 counts
        expression_data = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
        
        gene_symbols = ["G1", "G2", "G3"]
        
        df = pd.DataFrame({
            'sample_id': [f'sample_{i}' for i in range(3)],
            'tumor_type': ['BRCA'] * 3,
            'response_label': ['responder'] * 3,
            'gene_symbols': [gene_symbols] * 3,
            'expression_vector': expression_data
        })
        
        filtered_df, filtered_genes = filter_low_expression_genes(
            df, cpm_threshold=1.0, sample_fraction=0.8
        )
        
        # All genes should be filtered out (0% expressed)
        assert len(filtered_genes) == 3
        assert filtered_df['gene_symbols'].iloc[0] == []

class TestLoadSaveProcessedData:
    """Tests for loading processed data."""

    def test_load_processed_data_missing_files(self, tmp_path):
        """Test behavior when processed data files are missing."""
        # Create a temporary project structure
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        
        # Don't create the sample files
        
        # Temporarily override get_project_root
        import src.config
        original_get_project_root = src.config.get_project_root
        src.config.get_project_root = lambda: tmp_path
        
        try:
            samples = load_processed_data()
            assert samples == {}
        finally:
            src.config.get_project_root = original_get_project_root