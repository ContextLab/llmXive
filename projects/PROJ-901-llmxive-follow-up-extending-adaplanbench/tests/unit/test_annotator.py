"""
Unit tests for the annotator module.
"""
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Import the functions to test
from dataset.annotator import (
    load_filtered_tasks,
    select_random_sample,
    save_annotation_sample
)
from config import Paths


class TestSelectRandomSample:
    """Tests for the select_random_sample function."""

    def test_sample_size_smaller_than_dataframe(self):
        """Test sampling when requested size is smaller than dataframe."""
        df = pd.DataFrame({"id": range(100), "value": range(100)})
        sample_size = 10
        sample_df = select_random_sample(df, sample_size, seed=42)
        
        assert len(sample_df) == sample_size
        assert all(idx in df.index for idx in sample_df.index)

    def test_sample_size_larger_than_dataframe(self):
        """Test sampling when requested size is larger than dataframe."""
        df = pd.DataFrame({"id": range(10), "value": range(10)})
        sample_size = 100
        sample_df = select_random_sample(df, sample_size, seed=42)
        
        assert len(sample_df) == len(df)

    def test_sample_size_equal_to_dataframe(self):
        """Test sampling when requested size equals dataframe size."""
        df = pd.DataFrame({"id": range(20), "value": range(20)})
        sample_size = 20
        sample_df = select_random_sample(df, sample_size, seed=42)
        
        assert len(sample_df) == sample_size

    def test_reproducibility_with_seed(self):
        """Test that same seed produces same sample."""
        df = pd.DataFrame({"id": range(50), "value": range(50)})
        
        sample1 = select_random_sample(df, 10, seed=123)
        sample2 = select_random_sample(df, 10, seed=123)
        
        assert sample1.equals(sample2)

    def test_different_seeds_produce_different_samples(self):
        """Test that different seeds produce different samples."""
        df = pd.DataFrame({"id": range(100), "value": range(100)})
        
        sample1 = select_random_sample(df, 10, seed=1)
        sample2 = select_random_sample(df, 10, seed=2)
        
        # They should be different (with very high probability)
        assert not sample1.equals(sample2)

    def test_sample_preserves_columns(self):
        """Test that sampled dataframe preserves all columns."""
        df = pd.DataFrame({
            "id": range(20),
            "task": ["task_" + str(i) for i in range(20)],
            "constraints": [i for i in range(20)]
        })
        
        sample_df = select_random_sample(df, 5, seed=42)
        
        assert set(sample_df.columns) == set(df.columns)

class TestSaveAnnotationSample:
    """Tests for the save_annotation_sample function."""

    def test_save_and_load(self):
        """Test that saved sample can be loaded correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_sample.csv"
            df = pd.DataFrame({"id": range(10), "value": range(10)})
            
            save_annotation_sample(df, output_path)
            
            assert output_path.exists()
            
            loaded_df = pd.read_csv(output_path)
            assert len(loaded_df) == len(df)
            assert set(loaded_df.columns) == set(df.columns)

    def test_creates_parent_directories(self):
        """Test that function creates parent directories if they don't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir1" / "subdir2" / "test.csv"
            df = pd.DataFrame({"id": [1], "value": [2]})
            
            save_annotation_sample(df, output_path)
            
            assert output_path.exists()