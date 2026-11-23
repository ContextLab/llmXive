import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils import get_data_qc_path
from code._02_preprocess import (
    filter_outliers_by_zscore,
    write_filtering_log,
    compute_z_scores
)

class TestOutlierFiltering:
    """Tests for outlier filtering logic (T015)."""

    def test_filter_outliers_zscore_3(self):
        """Test that outliers with z-score > 3 are removed."""
        # Create a dataset with known outliers
        data = {
            'value': [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]  # 100 is an outlier
        }
        df = pd.DataFrame(data)
        
        # Compute z-scores first
        df = compute_z_scores(df, 'value')
        
        # Filter outliers
        filtered_df, removed_count = filter_outliers_by_zscore(df, 'value', threshold=3.0)
        
        # Verify
        assert removed_count == 1, f"Expected 1 outlier removed, got {removed_count}"
        assert len(filtered_df) == 5, f"Expected 5 rows remaining, got {len(filtered_df)}"
        
        # Verify the outlier was actually removed
        assert 100.0 not in filtered_df['value'].values

    def test_filter_outliers_no_outliers(self):
        """Test that no outliers are removed when none exist."""
        data = {
            'value': [1.0, 2.0, 3.0, 4.0, 5.0]
        }
        df = pd.DataFrame(data)
        
        df = compute_z_scores(df, 'value')
        filtered_df, removed_count = filter_outliers_by_zscore(df, 'value', threshold=3.0)
        
        assert removed_count == 0
        assert len(filtered_df) == 5

    def test_write_filtering_log(self):
        """Test that filtering log is written correctly."""
        qc_dir = get_data_qc_path()
        qc_dir.mkdir(parents=True, exist_ok=True)
        log_path = qc_dir / "test_filtering_log.json"
        
        write_filtering_log(
            total_samples=100,
            removed_outliers=5,
            threshold=3.0,
            output_path=log_path
        )
        
        # Verify file exists
        assert log_path.exists(), "Filtering log file was not created"
        
        # Verify content
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        assert log_data['total_samples'] == 100
        assert log_data['removed_outliers'] == 5
        assert log_data['threshold'] == 3.0
        
        # Cleanup
        log_path.unlink()

    def test_zscore_computation(self):
        """Test z-score computation."""
        data = {'value': [10, 20, 30, 40, 50]}
        df = pd.DataFrame(data)
        
        df_z = compute_z_scores(df, 'value')
        
        # Check that z-score column exists
        assert 'value_z' in df_z.columns
        
        # Check that mean of z-scores is approximately 0
        assert abs(df_z['value_z'].mean()) < 1e-6
        
        # Check that std of z-scores is approximately 1
        assert abs(df_z['value_z'].std() - 1.0) < 1e-6

    def test_filter_outliers_edge_case_zero_std(self):
        """Test filtering when standard deviation is zero."""
        data = {'value': [5.0, 5.0, 5.0, 5.0]}
        df = pd.DataFrame(data)
        
        # This should handle zero std gracefully
        df_z = compute_z_scores(df, 'value')
        
        # All z-scores should be 0
        assert all(df_z['value_z'] == 0)
        
        # Filtering should remove nothing
        filtered_df, removed_count = filter_outliers_by_zscore(df_z, 'value', threshold=3.0)
        assert removed_count == 0
        assert len(filtered_df) == 4