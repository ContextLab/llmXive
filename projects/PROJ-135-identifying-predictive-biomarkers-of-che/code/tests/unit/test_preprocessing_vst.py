"""
Unit tests for VST and filtering logic in preprocessing.py.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.preprocessing import filter_low_expression_genes

class TestFilterLowExpressionGenes:
    @pytest.fixture
    def sample_counts(self):
        """Create a sample count matrix."""
        # 5 genes, 10 samples
        np.random.seed(42)
        data = np.random.poisson(10, (5, 10))
        # Make gene 0 very low expression (mostly zeros)
        data[0, :] = np.array([0, 0, 0, 0, 0, 1, 0, 0, 0, 0])
        # Make gene 1 low but passes threshold (2 samples > 0)
        data[1, :] = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0]) 
        
        df = pd.DataFrame(data, index=[f"Gene{i}" for i in range(5)], 
                          columns=[f"Sample{j}" for j in range(10)])
        return df
    
    def test_filter_logic(self, sample_counts):
        """Test that low expression genes are filtered correctly."""
        # CPM < 1 in > 80% samples should be removed.
        # 80% of 10 samples = 8 samples.
        # If a gene has CPM < 1 in 9 samples, it is removed.
        
        filtered = filter_low_expression_genes(sample_counts, cpm_threshold=1.0, sample_fraction=0.80)
        
        # Gene 0: 0 counts in 9 samples. CPM will be 0. 
        # 9/10 = 90% < 1. Should be removed.
        # Gene 1: 0 counts in 10 samples. Should be removed.
        # Others: Should remain.
        
        assert "Gene0" not in filtered.index
        assert "Gene1" not in filtered.index
        assert len(filtered) == 3
        
    def test_threshold_adjustment(self, sample_counts):
        """Test with a stricter threshold."""
        # If we require CPM >= 1 in 50% of samples (0.5)
        filtered = filter_low_expression_genes(sample_counts, cpm_threshold=1.0, sample_fraction=0.50)
        
        # Gene 0: 1 count in 1 sample. 1/10 = 10% >= 1. 
        # 90% < 1. 90% > 50%. Removed.
        # Gene 1: 0% >= 1. Removed.
        assert len(filtered) == 3

# Note: Full integration test for VST requires R and DESeq2 installed.
# The above tests verify the CPM filtering logic which is pure Python.
