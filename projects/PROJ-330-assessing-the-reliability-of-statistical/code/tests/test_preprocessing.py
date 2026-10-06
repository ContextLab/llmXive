"""
Tests for preprocessing module.
"""
import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
from src.preprocessing import stratify_samples, filter_zero_count_genes

class TestStratification:
    def test_stratification_handles_missing_batch(self):
        """Test that random fallback occurs when batch metadata is missing."""
        metadata = pd.DataFrame({"sample": ["s1", "s2", "s3", "s4", "s5"]})
        # No batch column provided
        subsets = stratify_samples(metadata, n_subsets=2, batch_column=None)
        assert len(subsets) == 2
        # Verify all samples are distributed
        all_samples = []
        for subset in subsets.values():
            all_samples.extend(subset.index.tolist())
        assert set(all_samples) == set(metadata.index.tolist())

class TestZeroCountFiltering:
    def test_filters_zero_count_genes(self):
        """Test that genes with zero counts are removed."""
        data = {"s1": [0, 1, 2], "s2": [0, 2, 3]}
        df = pd.DataFrame(data, index=["g1", "g2", "g3"])
        filtered = filter_zero_count_genes(df)
        assert "g1" not in filtered.index
        assert "g2" in filtered.index
        assert "g3" in filtered.index

class TestPreprocessingIntegration:
    def test_full_pipeline(self):
        """Test full preprocessing pipeline."""
        counts = pd.DataFrame({"s1": [0, 1, 2], "s2": [0, 2, 3]}, index=["g1", "g2", "g3"])
        meta = pd.DataFrame({"batch": ["A", "B", "A"]}, index=["s1", "s2", "s3"])
        filtered, subsets = preprocess_dataset(counts, meta, batch_column="batch", n_subsets=2)
        assert len(filtered) < len(counts)
        assert len(subsets) == 2
