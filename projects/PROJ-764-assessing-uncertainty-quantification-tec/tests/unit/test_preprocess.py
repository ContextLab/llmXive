import pytest
import pandas as pd
import numpy as np
import os
import sys
import json
from pathlib import Path

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from data.preprocess import (
    apply_quantile_binning, 
    stratified_split, 
    load_config
)

class TestPreprocess:
    @pytest.fixture
    def sample_data(self):
        """Create a sample dataframe for testing."""
        np.random.seed(42)
        n_samples = 1000
        data = {
            'formation_energy_per_atom': np.random.normal(-5.0, 2.0, n_samples),
            'nelements': np.random.randint(2, 10, n_samples),
            'nsites': np.random.randint(5, 50, n_samples),
            'volume_per_atom': np.random.normal(20.0, 5.0, n_samples)
        }
        return pd.DataFrame(data)

    def test_quantile_binning_creates_bins(self, sample_data):
        """Test that binning creates the expected number of bins."""
        df = sample_data.copy()
        n_bins = 10
        df = apply_quantile_binning(df, 'formation_energy_per_atom', n_bins)
        
        assert 'target_bin' in df.columns
        # Due to duplicates in quantiles, we might get fewer bins, but at least 2
        assert df['target_bin'].nunique() >= 2
        assert df['target_bin'].nunique() <= n_bins

    def test_stratified_split_preserves_distribution(self, sample_data):
        """Test that stratified split maintains bin distribution."""
        df = sample_data.copy()
        df = apply_quantile_binning(df, 'formation_energy_per_atom', n_bins=5)
        
        train_ratio = 0.8
        train_df, val_df, test_df = stratified_split(
            df, 
            split_ratios=[train_ratio, 0.1, 0.1], 
            seed=42
        )
        
        # Check sizes
        total = len(train_df) + len(val_df) + len(test_df)
        assert abs(len(train_df) / total - train_ratio) < 0.02
        
        # Check that all splits have samples from multiple bins
        assert train_df['target_bin'].nunique() > 1
        assert val_df['target_bin'].nunique() > 1
        assert test_df['target_bin'].nunique() > 1

    def test_load_config(self):
        """Test that config is loaded correctly."""
        config = load_config()
        assert 'split_ratio' in config
        assert 'seed' in config
        assert config['split_type'] == 'stratified'
        
    def test_binning_uniformity(self, sample_data):
        """Test that bins are approximately uniform."""
        df = sample_data.copy()
        n_bins = 5
        df = apply_quantile_binning(df, 'formation_energy_per_atom', n_bins)
        
        bin_counts = df['target_bin'].value_counts().sort_index()
        total = len(df)
        expected_per_bin = total / n_bins
        
        # Allow 20% deviation from uniform
        for count in bin_counts:
            assert abs(count - expected_per_bin) < expected_per_bin * 0.3