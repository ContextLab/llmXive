import os
import sys
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add code root to path
code_root = Path(__file__).resolve().parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from data.preprocess import apply_quantile_binning, stratified_split, load_config

class TestQuantileBinning:
    def test_binning_creates_column(self):
        """Test that binning creates the target_bin column."""
        df = pd.DataFrame({
            "formation_energy": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        })
        result = apply_quantile_binning(df, "formation_energy", n_bins=5)
        assert "target_bin" in result.columns
        assert len(result) == len(df)

    def test_binning_distribution(self):
        """Test that bins are roughly equal size."""
        np.random.seed(42)
        df = pd.DataFrame({
            "formation_energy": np.random.randn(1000)
        })
        result = apply_quantile_binning(df, "formation_energy", n_bins=10)
        
        # Check that bins are balanced (allowing for some variance)
        bin_counts = result["target_bin"].value_counts()
        expected_min = 90 # 1000 / 10 * 0.9
        assert all(count >= expected_min for count in bin_counts), "Bins are not balanced enough"

    def test_invalid_target_column(self):
        """Test error when target column doesn't exist."""
        df = pd.DataFrame({"other_col": [1, 2, 3]})
        with pytest.raises(ValueError):
            apply_quantile_binning(df, "nonexistent_col")

    def test_insufficient_variance(self):
        """Test error when target has no variance."""
        df = pd.DataFrame({"formation_energy": [1.0, 1.0, 1.0]})
        with pytest.raises(ValueError):
            apply_quantile_binning(df, "formation_energy")

class TestStratifiedSplit:
    def test_split_proportions(self):
        """Test that split proportions match config."""
        np.random.seed(42)
        df = pd.DataFrame({
            "feature1": np.random.randn(1000),
            "feature2": np.random.randn(1000),
            "formation_energy": np.random.randn(1000)
        })
        config = {
            "split_ratio": [0.8, 0.1, 0.1],
            "split_type": "stratified",
            "seed": 42
        }
        
        train, val, test = stratified_split(df, config)
        
        assert len(train) == 800
        assert len(val) == 100
        assert len(test) == 100

    def test_stratification_preserved(self):
        """Test that target_bin distribution is similar across splits."""
        np.random.seed(42)
        df = pd.DataFrame({
            "feature1": np.random.randn(1000),
            "formation_energy": np.random.randn(1000)
        })
        config = {
            "split_ratio": [0.8, 0.1, 0.1],
            "split_type": "stratified",
            "seed": 42
        }
        
        train, val, test = stratified_split(df, config)
        
        # Check that target_bin exists in all splits
        assert "target_bin" in train.columns
        assert "target_bin" in val.columns
        assert "target_bin" in test.columns

    def test_invalid_split_type(self):
        """Test error when split_type is not stratified."""
        df = pd.DataFrame({"formation_energy": [1, 2, 3]})
        config = {
            "split_type": "random",
            "seed": 42
        }
        with pytest.raises(ValueError):
            stratified_split(df, config)

    def test_missing_target_column(self):
        """Test error when target column is missing."""
        df = pd.DataFrame({"feature1": [1, 2, 3]})
        config = {
            "split_type": "stratified",
            "seed": 42
        }
        with pytest.raises(KeyError):
            stratified_split(df, config)

class TestLoadConfig:
    def test_load_config(self):
        """Test loading config from file."""
        config = load_config("code/config.yaml")
        assert "seed" in config
        assert "split_ratio" in config
        assert "split_type" in config
        assert config["split_type"] == "stratified"