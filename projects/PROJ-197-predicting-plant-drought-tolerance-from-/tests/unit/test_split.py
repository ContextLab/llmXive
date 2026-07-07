"""
Unit tests for the data splitting module.

Tests stratified split logic, fallback to leave-one-out,
and edge cases.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.split import perform_stratified_split, _perform_leave_one_out_split, save_split_metadata


class TestStratifiedSplit:
    """Test cases for stratified split functionality."""

    def test_stratified_split_balanced(self):
        """Test stratified split with balanced dataset."""
        # Create balanced dataset
        data = {
            "species_id": [f"sp_{i}" for i in range(100)],
            "trait_1": np.random.randn(100),
            "label": [0] * 50 + [1] * 50
        }
        df = pd.DataFrame(data)
        
        train_df, test_df = perform_stratified_split(
            df,
            label_col="label",
            test_size=0.2,
            random_state=42
        )
        
        # Check sizes
        assert len(train_df) == 80
        assert len(test_df) == 20
        
        # Check label distribution is approximately maintained
        train_ratio = train_df["label"].mean()
        test_ratio = test_df["label"].mean()
        original_ratio = df["label"].mean()
        
        # Allow some tolerance due to random sampling
        assert abs(train_ratio - original_ratio) < 0.1
        assert abs(test_ratio - original_ratio) < 0.1

    def test_stratified_split_imbalanced(self):
        """Test stratified split with imbalanced dataset."""
        # Create imbalanced dataset (80% class 0, 20% class 1)
        n_samples = 100
        data = {
            "species_id": [f"sp_{i}" for i in range(n_samples)],
            "trait_1": np.random.randn(n_samples),
            "label": [0] * 80 + [1] * 20
        }
        df = pd.DataFrame(data)
        
        train_df, test_df = perform_stratified_split(
            df,
            label_col="label",
            test_size=0.3,
            random_state=42
        )
        
        # Check sizes
        assert len(train_df) == 70
        assert len(test_df) == 30
        
        # Both classes should be present in both splits
        assert 0 in train_df["label"].values
        assert 1 in train_df["label"].values
        assert 0 in test_df["label"].values
        assert 1 in test_df["label"].values

    def test_stratified_split_reproducibility(self):
        """Test that split is reproducible with same random state."""
        data = {
            "species_id": [f"sp_{i}" for i in range(50)],
            "trait_1": np.random.randn(50),
            "label": [0] * 25 + [1] * 25
        }
        df = pd.DataFrame(data)
        
        train1, test1 = perform_stratified_split(df, random_state=123)
        train2, test2 = perform_stratified_split(df, random_state=123)
        
        # Should be identical
        pd.testing.assert_frame_equal(train1, train2)
        pd.testing.assert_frame_equal(test1, test2)


class TestLeaveOneOutFallback:
    """Test cases for leave-one-out fallback."""

    def test_small_dataset_fallback(self):
        """Test that small dataset triggers fallback."""
        # Create small dataset (< 10 samples)
        data = {
            "species_id": [f"sp_{i}" for i in range(5)],
            "trait_1": np.random.randn(5),
            "label": [0, 0, 0, 1, 1]
        }
        df = pd.DataFrame(data)
        
        train_df, test_df = perform_stratified_split(
            df,
            label_col="label",
            min_samples_per_class=5
        )
        
        # Should have triggered fallback
        # Test set should have at least one sample per class
        assert len(test_df) >= 2  # At least one per class
        assert len(train_df) < 5

    def test_insufficient_samples_per_class(self):
        """Test fallback when one class has too few samples."""
        # Create dataset where one class has only 2 samples
        data = {
            "species_id": [f"sp_{i}" for i in range(20)],
            "trait_1": np.random.randn(20),
            "label": [0] * 18 + [1] * 2
        }
        df = pd.DataFrame(data)
        
        train_df, test_df = perform_stratified_split(
            df,
            label_col="label",
            min_samples_per_class=5
        )
        
        # Should have triggered fallback
        assert len(test_df) >= 2  # At least one per class

    def test_very_small_dataset(self):
        """Test edge case with extremely small dataset."""
        data = {
            "species_id": [f"sp_{i}" for i in range(3)],
            "trait_1": np.random.randn(3),
            "label": [0, 0, 1]
        }
        df = pd.DataFrame(data)
        
        train_df, test_df = _perform_leave_one_out_split(df, "label")
        
        # Test set should have one sample per class
        assert len(test_df) == 2
        assert len(train_df) == 1


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame(columns=["species_id", "trait_1", "label"])
        
        with pytest.raises(ValueError, match="empty"):
            perform_stratified_split(df, "label")

    def test_missing_label_column(self):
        """Test handling of missing label column."""
        data = {
            "species_id": [f"sp_{i}" for i in range(10)],
            "trait_1": np.random.randn(10)
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="not found"):
            perform_stratified_split(df, "label")

    def test_single_class_dataset(self):
        """Test handling of dataset with only one class."""
        data = {
            "species_id": [f"sp_{i}" for i in range(20)],
            "trait_1": np.random.randn(20),
            "label": [0] * 20
        }
        df = pd.DataFrame(data)
        
        # This should trigger fallback since stratification will fail
        train_df, test_df = perform_stratified_split(
            df,
            label_col="label",
            min_samples_per_class=5
        )
        
        # Should still produce splits
        assert len(train_df) + len(test_df) == 20


class TestSaveSplitMetadata:
    """Test metadata saving functionality."""

    def test_save_metadata_creates_file(self, tmp_path):
        """Test that metadata file is created correctly."""
        data = {
            "species_id": [f"sp_{i}" for i in range(10)],
            "trait_1": np.random.randn(10),
            "label": [0] * 5 + [1] * 5
        }
        df = pd.DataFrame(data)
        
        train_df = df.iloc[:8]
        test_df = df.iloc[8:]
        
        metadata_path = tmp_path / "metadata.json"
        save_split_metadata(train_df, test_df, metadata_path, "stratified")
        
        assert metadata_path.exists()
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert metadata["split_method"] == "stratified"
        assert metadata["train_samples"] == 8
        assert metadata["test_samples"] == 2
        assert "timestamp" in metadata
        assert "train_label_distribution" in metadata
        assert "test_label_distribution" in metadata