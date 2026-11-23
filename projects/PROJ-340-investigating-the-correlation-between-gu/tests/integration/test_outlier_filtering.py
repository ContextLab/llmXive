import os
import sys
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from ingest import detect_outliers_iqr, filter_outliers, save_outlier_report, save_filtered_data

class TestOutlierFiltering:
    @pytest.fixture
    def sample_data(self):
        """Create a sample dataframe with known outliers."""
        np.random.seed(42)
        n = 100
        # Normal data
        data = np.random.normal(loc=10, scale=1, size=(n, 2))
        # Inject outliers
        data[0, 0] = 50.0   # Extreme high outlier
        data[1, 1] = -40.0  # Extreme low outlier
        data[2, 0] = 10.5   # Normal
        data[3, 1] = 9.8    # Normal

        df = pd.DataFrame(data, columns=['col_A', 'col_B'])
        return df

    @pytest.fixture
    def temp_output_dir(self, tmp_path):
        """Create a temporary directory for output files."""
        output_dir = tmp_path / "data" / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    def test_detect_outliers_iqr(self, sample_data):
        """Test that IQR detection correctly identifies injected outliers."""
        outlier_mask = detect_outliers_iqr(sample_data)
        
        # Row 0 and Row 1 should be outliers
        assert outlier_mask.iloc[0] is True, "Row 0 (extreme high) should be detected as outlier"
        assert outlier_mask.iloc[1] is True, "Row 1 (extreme low) should be detected as outlier"
        
        # Row 2 and 3 should be normal
        assert outlier_mask.iloc[2] is False, "Row 2 should not be an outlier"
        assert outlier_mask.iloc[3] is False, "Row 3 should not be an outlier"

    def test_filter_outliers(self, sample_data):
        """Test that filtering removes only the outlier rows."""
        outlier_mask = detect_outliers_iqr(sample_data)
        filtered_df = filter_outliers(sample_data, outlier_mask)
        
        # Original length 100, 2 outliers -> 98
        assert len(filtered_df) == len(sample_data) - 2, "Filtered dataframe should have 2 fewer rows"
        
        # Check that indices 0 and 1 are not present
        assert 0 not in filtered_df.index
        assert 1 not in filtered_df.index

    def test_save_outlier_report(self, sample_data, temp_output_dir):
        """Test that the outlier report is saved correctly."""
        outlier_mask = detect_outliers_iqr(sample_data)
        output_path = str(temp_output_dir / "outlier_report.json")
        
        save_outlier_report(outlier_mask, output_path)
        
        assert os.path.exists(output_path), "Outlier report file should exist"
        
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        assert "count" in report
        assert "excluded_indices" in report
        assert report["count"] == 2
        assert 0 in report["excluded_indices"]
        assert 1 in report["excluded_indices"]

    def test_save_filtered_data(self, sample_data, temp_output_dir):
        """Test that filtered data is saved to parquet."""
        outlier_mask = detect_outliers_iqr(sample_data)
        filtered_df = filter_outliers(sample_data, outlier_mask)
        output_path = str(temp_output_dir / "filtered_data.parquet")
        
        save_filtered_data(filtered_df, output_path)
        
        assert os.path.exists(output_path), "Filtered data file should exist"
        
        loaded_df = pd.read_parquet(output_path)
        assert len(loaded_df) == len(filtered_df)
        assert list(loaded_df.columns) == list(filtered_df.columns)