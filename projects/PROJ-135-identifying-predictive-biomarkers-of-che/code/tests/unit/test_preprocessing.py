import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the function to test
from src.preprocessing import filter_low_expression_genes, process_tumor_type

class TestFilterLowExpressionGenes:
    def test_filter_keeps_high_expression_genes(self):
        """
        Test that genes with high expression (CPM >= 1 in most samples) are kept.
        """
        # Create a mock DataFrame: 3 genes, 5 samples
        # Gene A: High expression (CPM=10 in all samples) -> Should KEEP
        # Gene B: Mixed (CPM=10 in 2, CPM=0 in 3) -> 60% low. Threshold is 80% low to remove. 
        #         60% < 80%, so we KEEP.
        # Gene C: Low expression (CPM=0 in all samples) -> 100% low. > 80%, so REMOVE.
        
        data = {
            'gene_symbol': ['GeneA', 'GeneB', 'GeneC'],
            'Sample1': [1000000, 500000, 0],   # Counts -> CPM ~ 1000, 500, 0 (if total 1M)
            'Sample2': [1000000, 500000, 0],
            'Sample3': [1000000, 0, 0],
            'Sample4': [1000000, 0, 0],
            'Sample5': [1000000, 0, 0]
        }
        df = pd.DataFrame(data)
        
        # Total counts per row:
        # GeneA: 5M -> CPM = (1M/5M)*1M = 200,000 (High)
        # GeneB: 1M -> CPM = (0.5M/1M)*1M = 500,000 (High) for 2 samples, 0 for 3
        # GeneC: 0 -> CPM = 0
        
        # Wait, CPM calculation in code: sum(axis=1). 
        # GeneA sum = 5,000,000. CPM = 1,000,000 / 5,000,000 * 1,000,000 = 200,000.
        # GeneB sum = 1,000,000. CPM = 500,000 / 1,000,000 * 1,000,000 = 500,000.
        # GeneC sum = 0. CPM = 0.
        
        # All non-zero CPMs are > 1.
        # GeneA: 0% low (Keep)
        # GeneB: 3/5 = 60% low (Keep, since 60 <= 80)
        # GeneC: 100% low (Remove, since 100 > 80)
        
        result = filter_low_expression_genes(df, cpm_threshold=1.0, sample_fraction_threshold=0.80)
        
        assert len(result) == 2
        assert 'GeneA' in result['gene_symbol'].values
        assert 'GeneB' in result['gene_symbol'].values
        assert 'GeneC' not in result['gene_symbol'].values

    def test_filter_removes_low_expression_genes(self):
        """
        Test that genes with low expression (CPM < 1 in >80% samples) are removed.
        """
        data = {
            'gene_symbol': ['LowGene'],
            'S1': [10], # Total 10 -> CPM = 1M. Wait, if total is small, CPM is high.
            'S2': [10],
            'S3': [10],
            'S4': [10],
            'S5': [10]
        }
        # This creates high CPM. Let's construct raw counts that result in low CPM.
        # To get CPM < 1, we need Count / Total < 1e-6.
        # If Total = 10,000,000, then Count < 10.
        # Let's make a gene with 0 counts in 4/5 samples.
        # Sample 1: 10 counts. Sample 2-5: 0 counts.
        # Row sum = 10.
        # CPM for S1 = (10/10)*1M = 1,000,000 (High)
        # CPM for S2-5 = 0 (Low)
        # Fraction low = 4/5 = 0.8. 
        # Threshold is > 0.8 to remove. 0.8 is NOT > 0.8. So it stays.
        # Let's make 4/5 samples 0, but wait, 4/5 is exactly 0.8.
        # Condition: Remove if fraction_low > 0.8.
        # If 4/5 = 0.8, it is NOT > 0.8. Kept.
        # If 5/5 = 1.0, it is > 0.8. Removed.
        
        # Let's test the boundary: 90% low.
        data = {
            'gene_symbol': ['VeryLowGene'],
            'S1': [10], # CPM High
            'S2': [0],
            'S3': [0],
            'S4': [0],
            'S5': [0],
            'S6': [0],
            'S7': [0],
            'S8': [0],
            'S9': [0],
            'S10': [0]
        }
        # 9/10 = 0.9 low. 0.9 > 0.8. Should be removed.
        df = pd.DataFrame(data)
        result = filter_low_expression_genes(df, cpm_threshold=1.0, sample_fraction_threshold=0.80)
        assert len(result) == 0

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=['gene_symbol', 'S1'])
        result = filter_low_expression_genes(df)
        assert result.empty

    def test_no_sample_columns(self):
        df = pd.DataFrame({'gene_symbol': ['A']})
        with pytest.raises(ValueError):
            filter_low_expression_genes(df)