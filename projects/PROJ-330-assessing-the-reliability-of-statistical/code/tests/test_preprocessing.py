import os
import tempfile
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

from src.preprocessing import (
    filter_zero_count_genes,
    stratify_samples,
    preprocess_dataset
)

class TestZeroCountFiltering:
    def test_filter_zero_count_genes(self):
        df = pd.DataFrame({
            's1': [1, 0, 0],
            's2': [2, 0, 0],
            's3': [0, 0, 0]
        }, index=['g1', 'g2', 'g3'])
        filtered = filter_zero_count_genes(df)
        assert len(filtered) == 1
        assert 'g1' in filtered.index

class TestStratification:
    def test_stratification_with_batch(self):
        df = pd.DataFrame(np.random.rand(10, 3), index=[f's{i}' for i in range(10)])
        meta = pd.DataFrame({'batch': ['A']*5 + ['B']*5}, index=df.index)
        subsets = stratify_samples(df, meta, n_splits=2)
        assert len(subsets) == 2
        assert len(subsets[0]) + len(subsets[1]) == 10

    def test_stratification_without_batch(self):
        df = pd.DataFrame(np.random.rand(10, 3), index=[f's{i}' for i in range(10)])
        subsets = stratify_samples(df, None, n_splits=2)
        assert len(subsets) == 2
        # Check all samples are present
        all_samples = []
        for s in subsets:
            all_samples.extend(s.index.tolist())
        assert sorted(all_samples) == sorted(df.index.tolist())

class TestPreprocessingIntegration:
    def test_preprocess_dataset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            counts_path = Path(tmpdir) / "counts.csv"
            df = pd.DataFrame({'s1': [1, 2], 's2': [3, 4]}, index=['g1', 'g2'])
            df.to_csv(counts_path)
            result_df, _ = preprocess_dataset(counts_path)
            assert result_df.shape == (2, 2)
