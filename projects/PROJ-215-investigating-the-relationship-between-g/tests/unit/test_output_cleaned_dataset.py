import pytest
import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.output_cleaned_dataset import load_preprocessed_data, merge_and_filter, verify_retention

class TestOutputCleanedDataset:
    
    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Create temporary directories for test data."""
        data_dir = tmp_path / "data" / "processed"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def test_load_preprocessed_data_csv(self, temp_dirs):
        """Test loading a CSV file."""
        df = pd.DataFrame({"sample_id": [1, 2], "value": [10, 20]})
        csv_path = temp_dirs / "test.csv"
        df.to_csv(csv_path, index=False)
        
        loaded = load_preprocessed_data(str(csv_path))
        assert loaded.shape == df.shape
        assert list(loaded.columns) == list(df.columns)

    def test_merge_and_filter(self, temp_dirs):
        """Test merging alpha metrics with preprocessed data."""
        # Create alpha metrics
        alpha_df = pd.DataFrame({
            "sample_id": [1, 2, 3],
            "shannon": [2.5, 3.0, 1.5]
        })
        alpha_path = temp_dirs / "alpha.csv"
        alpha_df.to_csv(alpha_path, index=False)
        
        # Create preprocessed data
        pre_df = pd.DataFrame({
            "sample_id": [1, 2, 4],
            "phq9": [5, 10, 2],
            "gad7": [3, 8, 1]
        })
        pre_path = temp_dirs / "pre.csv"
        pre_df.to_csv(pre_path, index=False)
        
        merged = merge_and_filter(str(alpha_path), str(pre_path))
        
        # Should have 2 rows (sample_id 1 and 2)
        assert len(merged) == 2
        assert "shannon" in merged.columns
        assert "phq9" in merged.columns

    def test_verify_retention_pass(self, temp_dirs):
        """Test verification when criteria are met."""
        df = pd.DataFrame({
            "sample_id": range(100),
            "phq9": [5] * 100,
            "gad7": [3] * 100
        })
        initial = 100
        
        rate, rows, is_valid = verify_retention(df, initial)
        
        assert rate == 100.0
        assert rows == 100
        assert is_valid is True

    def test_verify_retention_fail_low_rows(self, temp_dirs):
        """Test verification when row count is too low."""
        df = pd.DataFrame({
            "sample_id": range(50),
            "phq9": [5] * 50,
            "gad7": [3] * 50
        })
        initial = 100
        
        rate, rows, is_valid = verify_retention(df, initial)
        
        assert rate == 50.0
        assert rows == 50
        assert is_valid is False

    def test_verify_retention_fail_missing_values(self, temp_dirs):
        """Test verification when key columns have missing values."""
        df = pd.DataFrame({
            "sample_id": [1, 2, 3],
            "phq9": [5, np.nan, 10],
            "gad7": [3, 4, 5]
        })
        initial = 3
        
        rate, rows, is_valid = verify_retention(df, initial)
        
        # Only 2 valid rows
        assert rows == 2
        assert rate == (2/3)*100
        # If initial was 3, 2/3 is 66.6%, which is < 80% -> False
        assert is_valid is False