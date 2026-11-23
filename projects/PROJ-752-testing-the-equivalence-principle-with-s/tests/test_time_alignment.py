import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data.preprocessing import merge_multi_satellite_datasets, align_time_series, AnalysisError

class TestTimeAlignment:
    def test_merge_multi_satellite_datasets_basic(self):
        """Test basic merging of two satellite datasets."""
        # Satellite A
        df_a = pd.DataFrame({
            'time': [datetime(2023, 1, 1, 12, 0, 0), datetime(2023, 1, 1, 12, 0, 5)],
            'satellite_id': ['A', 'A'],
            'residual_m': [0.1, 0.2]
        })
        
        # Satellite B (overlapping and non-overlapping times)
        df_b = pd.DataFrame({
            'time': [datetime(2023, 1, 1, 12, 0, 2), datetime(2023, 1, 1, 12, 0, 10)],
            'satellite_id': ['B', 'B'],
            'residual_m': [0.3, 0.4]
        })
        
        result = merge_multi_satellite_datasets([df_a, df_b])
        
        assert len(result) == 4
        assert list(result['satellite_id']) == ['A', 'A', 'B', 'B'] or \
               list(result['satellite_id']) == ['A', 'B', 'A', 'B'] # Order depends on sort
        
        # Check sorting
        times = result['time'].tolist()
        assert times == sorted(times), "Result must be sorted by time"

    def test_merge_empty_list(self):
        """Test error handling for empty input list."""
        with pytest.raises(AnalysisError):
            merge_multi_satellite_datasets([])

    def test_merge_missing_satellite_id(self):
        """Test error handling for missing satellite_id column."""
        df = pd.DataFrame({
            'time': [datetime(2023, 1, 1)],
            'residual_m': [0.1]
        })
        with pytest.raises(AnalysisError):
            merge_multi_satellite_datasets([df])

    def test_merge_missing_time_column(self):
        """Test error handling for missing time column."""
        df = pd.DataFrame({
            'satellite_id': ['A'],
            'residual_m': [0.1]
        })
        with pytest.raises(AnalysisError):
            merge_multi_satellite_datasets([df])

    def test_align_time_series_sorting(self):
        """Test that align_time_series sorts correctly."""
        df = pd.DataFrame({
            'time': [datetime(2023, 1, 1, 12, 0, 5), datetime(2023, 1, 1, 12, 0, 1)],
            'val': [1, 2]
        })
        
        result = align_time_series(df)
        times = result['time'].tolist()
        assert times == sorted(times)

    def test_align_time_series_missing_col(self):
        """Test error handling for missing time column in alignment."""
        df = pd.DataFrame({'val': [1, 2]})
        with pytest.raises(AnalysisError):
            align_time_series(df, time_col='time')

    def test_merge_single_dataframe(self):
        """Test merging a single dataframe just sorts it."""
        df = pd.DataFrame({
            'time': [datetime(2023, 1, 1, 12, 0, 5), datetime(2023, 1, 1, 12, 0, 1)],
            'satellite_id': ['A', 'A'],
            'residual_m': [0.1, 0.2]
        })
        
        result = merge_multi_satellite_datasets([df])
        assert len(result) == 2
        times = result['time'].tolist()
        assert times == sorted(times)