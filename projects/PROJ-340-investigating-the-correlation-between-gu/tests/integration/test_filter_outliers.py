import pytest
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
from ingest import filter_outliers, save_outlier_report, save_filtered_data, detect_outliers_iqr

class TestFilterOutliers:
    
    def setup_method(self):
        """Setup test data with known outliers."""
        # Create a DataFrame with a clear outlier
        data = {
            'A': [10, 12, 11, 13, 12, 100], # 100 is an outlier
            'B': [20, 21, 19, 22, 20, 21],
            'C': [5, 6, 5, 4, 5, 5]
        }
        self.df = pd.DataFrame(data)
        self.expected_excluded_count = 1
        self.expected_excluded_index = 5 # Last row

    def test_detect_outliers_iqr(self):
        """Test that IQR detection correctly identifies the outlier."""
        mask = detect_outliers_iqr(self.df)
        assert mask.sum() == 1, f"Expected 1 outlier, found {mask.sum()}"
        assert mask.iloc[5] == True, "Row 5 should be flagged as outlier"

    def test_filter_outliers_function(self):
        """Test that filter_outliers removes the flagged row and returns correct indices."""
        mask = detect_outliers_iqr(self.df)
        filtered_df, excluded_indices = filter_outliers(self.df, mask)
        
        assert len(filtered_df) == len(self.df) - 1, "One row should be removed"
        assert self.expected_excluded_index in excluded_indices, "Excluded indices should contain index 5"
        assert len(excluded_indices) == 1, "Should have exactly one excluded index"
        
        # Verify the outlier is gone
        assert 100 not in filtered_df['A'].values, "Outlier value 100 should not be in filtered data"

    def test_save_outlier_report(self, tmp_path):
        """Test that save_outlier_report writes the correct JSON structure."""
        output_file = tmp_path / "outlier_report.json"
        excluded_indices = [5, 10]
        
        save_outlier_report(excluded_indices, str(output_file))
        
        assert output_file.exists(), "Report file should be created"
        
        with open(output_file, 'r') as f:
            report = json.load(f)
        
        assert report['count'] == 2, "Count should match list length"
        assert report['excluded_indices'] == [5, 10], "Indices should match"

    def test_save_filtered_data(self, tmp_path):
        """Test that save_filtered_data creates a valid parquet file."""
        output_file = tmp_path / "filtered_data.parquet"
        mask = detect_outliers_iqr(self.df)
        filtered_df, _ = filter_outliers(self.df, mask)
        
        save_filtered_data(filtered_df, str(output_file))
        
        assert output_file.exists(), "Parquet file should be created"
        
        # Reload and verify
        loaded_df = pd.read_parquet(output_file)
        assert len(loaded_df) == len(filtered_df), "Loaded data should match filtered data"
        assert list(loaded_df.columns) == list(filtered_df.columns), "Columns should match"