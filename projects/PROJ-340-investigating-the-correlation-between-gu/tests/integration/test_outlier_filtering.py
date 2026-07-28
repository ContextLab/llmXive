import os
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import pytest
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingest import filter_outliers, save_outlier_report, save_filtered_data, detect_outliers_iqr

class TestOutlierFiltering:
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.tmp_path = tmp_path
        self.data_dir = tmp_path / 'data' / 'processed'
        self.results_dir = tmp_path / 'data' / 'results'
        self.data_dir.mkdir(parents=True)
        self.results_dir.mkdir(parents=True)
        yield

    def test_detect_outliers_iqr_basic(self):
        """Test basic IQR outlier detection."""
        data = pd.DataFrame({
            'values': [10, 11, 12, 13, 14, 100] # 100 is an outlier
        })
        indices = detect_outliers_iqr(data, 'values')
        assert len(indices) == 1
        assert indices[0] == 5

    def test_filter_outliers_removes_points(self):
        """Test that filter_outliers correctly removes flagged points."""
        # Create data with known outliers
        # Q1=11, Q3=13, IQR=2. Bounds: 8 to 16. 20 is outlier.
        data = pd.DataFrame({
            'subject_id': [1, 2, 3, 4, 5],
            'metric': [11, 12, 13, 14, 20] 
        })
        
        filtered_df, report = filter_outliers(data, ['metric'])
        
        assert len(filtered_df) == 4
        assert report['count'] == 1
        assert 4 in report['excluded_indices'] # Row index 4 (value 20)
        assert 20 not in filtered_df['metric'].values

    def test_filter_outliers_preserves_non_outliers(self):
        """Test that non-outliers are preserved."""
        data = pd.DataFrame({
            'metric': [10, 11, 12, 13, 14]
        })
        
        filtered_df, report = filter_outliers(data, ['metric'])
        
        assert len(filtered_df) == 5
        assert report['count'] == 0
        assert len(report['excluded_indices']) == 0

    def test_save_outlier_report(self):
        """Test saving the outlier report JSON."""
        report = {
            'count': 2,
            'excluded_indices': [0, 5]
        }
        output_path = str(self.results_dir / 'outlier_report.json')
        
        save_outlier_report(report, output_path)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['count'] == 2
        assert loaded['excluded_indices'] == [0, 5]

    def test_save_filtered_data_parquet(self):
        """Test saving filtered data to parquet."""
        data = pd.DataFrame({
            'id': [1, 2, 3],
            'val': [10.0, 20.0, 30.0]
        })
        output_path = str(self.data_dir / 'filtered_data.parquet')
        
        save_filtered_data(data, output_path)
        
        assert os.path.exists(output_path)
        loaded = pd.read_parquet(output_path)
        assert loaded.shape == data.shape
        assert list(loaded.columns) == list(data.columns)

    def test_full_flow_integration(self):
        """Integration test: detect, filter, and save."""
        # Setup
        data = pd.DataFrame({
            'id': range(10),
            'sleep_duration': [7.0, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 15.0] # 15.0 is outlier
        })
        
        # Filter
        filtered_df, report = filter_outliers(data, ['sleep_duration'])
        
        # Save
        save_outlier_report(report, str(self.results_dir / 'outlier_report.json'))
        save_filtered_data(filtered_df, str(self.data_dir / 'filtered_data.parquet'))
        
        # Verify
        assert report['count'] == 1
        assert 9 in report['excluded_indices']
        assert len(filtered_df) == 9
        
        # Verify file contents
        loaded_df = pd.read_parquet(str(self.data_dir / 'filtered_data.parquet'))
        assert len(loaded_df) == 9
        assert 15.0 not in loaded_df['sleep_duration'].values