"""
Unit tests for code/modeling/filter.py.
Tests dataset filtering based on validation flags.
"""
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
import tempfile

from modeling.filter import (
    load_pre_filter_dataset,
    filter_samples,
    write_filtered_dataset
)

class TestLoadPreFilterDataset:
    def test_load_pre_filter_dataset(self):
        """Should load a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_data.csv"
            df = pd.DataFrame({
                "sample_id": ["s1", "s2", "s3"],
                "PCE": [10.0, 15.0, 12.0],
                "validation_flag": [0, 1, 0],
                "depth_flag": [0, 0, 1]
            })
            df.to_csv(csv_path, index=False)
            
            result = load_pre_filter_dataset(str(csv_path))
            assert result is not None
            assert len(result) == 3
            assert "validation_flag" in result.columns

class TestFilterSamples:
    def test_filter_samples_removes_invalid(self):
        """Should remove samples with validation_flag=1 or depth_flag=1."""
        df = pd.DataFrame({
            "sample_id": ["s1", "s2", "s3", "s4"],
            "PCE": [10.0, 15.0, 12.0, 11.0],
            "validation_flag": [0, 1, 0, 0],
            "depth_flag": [0, 0, 1, 0]
        })
        
        filtered = filter_samples(df)
        assert len(filtered) == 2
        assert "s2" not in filtered["sample_id"].values
        assert "s3" not in filtered["sample_id"].values
        assert "s1" in filtered["sample_id"].values
        assert "s4" in filtered["sample_id"].values

    def test_filter_samples_all_valid(self):
        """Should keep all samples if all flags are 0."""
        df = pd.DataFrame({
            "sample_id": ["s1", "s2"],
            "PCE": [10.0, 15.0],
            "validation_flag": [0, 0],
            "depth_flag": [0, 0]
        })
        
        filtered = filter_samples(df)
        assert len(filtered) == 2

    def test_filter_samples_all_invalid(self):
        """Should return empty DataFrame if all flags are 1."""
        df = pd.DataFrame({
            "sample_id": ["s1", "s2"],
            "PCE": [10.0, 15.0],
            "validation_flag": [1, 1],
            "depth_flag": [1, 1]
        })
        
        filtered = filter_samples(df)
        assert len(filtered) == 0

    def test_filter_samples_missing_flags(self):
        """Should handle missing flag columns by treating as valid."""
        df = pd.DataFrame({
            "sample_id": ["s1", "s2"],
            "PCE": [10.0, 15.0]
            # No flags
        })
        
        filtered = filter_samples(df)
        # Should keep all if flags are missing (or treat as 0)
        assert len(filtered) == 2

class TestWriteFilteredDataset:
    def test_write_filtered_dataset_creates_file(self):
        """Should create the output CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            df = pd.DataFrame({
                "sample_id": ["s1", "s2"],
                "PCE": [10.0, 15.0]
            })
            output_path = Path(tmpdir) / "filtered.csv"
            
            write_filtered_dataset(df, str(output_path))
            assert output_path.exists()
            
            loaded = pd.read_csv(output_path)
            assert len(loaded) == 2
            assert "sample_id" in loaded.columns
