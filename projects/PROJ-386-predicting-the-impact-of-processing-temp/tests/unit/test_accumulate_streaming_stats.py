import pytest
import pandas as pd
import json
import os
import sys
from pathlib import Path
from io import StringIO

# Add code to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.ingestion import accumulate_streaming_stats, save_streaming_stats, RunningStats

class TestRunningStats:
    def test_single_update(self):
        stats = RunningStats()
        stats.update(10.0)
        assert stats.count == 1
        assert stats.mean == 10.0
        assert stats.null_count == 0

    def test_null_update(self):
        stats = RunningStats()
        stats.update(None)
        assert stats.count == 0
        assert stats.null_count == 1

    def test_multiple_updates(self):
        stats = RunningStats()
        for val in [10.0, 20.0, 30.0]:
            stats.update(val)
        assert stats.count == 3
        assert stats.mean == 20.0
        # Variance of [10, 20, 30] is 100
        assert abs(stats.get_variance() - 100.0) < 1e-6

    def test_min_max(self):
        stats = RunningStats()
        for val in [5.0, 15.0, 2.0, 20.0]:
            stats.update(val)
        assert stats.min_val == 2.0
        assert stats.max_val == 20.0

class TestAccumulateStreamingStats:
    def test_empty_iterable(self):
        stats = accumulate_streaming_stats(iter([]), ['col1'])
        assert stats['total_rows'] == 0
        assert stats['columns']['col1']['count'] == 0

    def test_single_chunk(self):
        df = pd.DataFrame({
            'Temp': [100.0, 200.0, 300.0],
            'Grain Size': [10.0, 20.0, 30.0]
        })
        result = accumulate_streaming_stats(iter([df]), ['Temp', 'Grain Size'])
        
        assert result['total_rows'] == 3
        assert result['columns']['Temp']['mean'] == 200.0
        assert result['columns']['Grain Size']['mean'] == 20.0
        assert result['columns']['Temp']['count'] == 3

    def test_multiple_chunks(self):
        chunks = [
            pd.DataFrame({'Temp': [100.0, 200.0]}),
            pd.DataFrame({'Temp': [300.0, 400.0]}),
            pd.DataFrame({'Temp': [500.0]})
        ]
        result = accumulate_streaming_stats(iter(chunks), ['Temp'])
        
        assert result['total_rows'] == 5
        assert result['columns']['Temp']['mean'] == 300.0 # (100+200+300+400+500)/5
        assert result['columns']['Temp']['count'] == 5

    def test_null_handling(self):
        chunks = [
            pd.DataFrame({'Temp': [100.0, None, 300.0]}),
            pd.DataFrame({'Temp': [None, 500.0]})
        ]
        result = accumulate_streaming_stats(iter(chunks), ['Temp'])
        
        assert result['total_rows'] == 5
        assert result['columns']['Temp']['count'] == 3 # Only non-null
        assert result['columns']['Temp']['null_count'] == 2
        assert result['columns']['Temp']['mean'] == 300.0 # (100+300+500)/3

    def test_missing_column_in_chunk(self):
        chunks = [
            pd.DataFrame({'Temp': [100.0], 'Grain Size': [10.0]}),
            pd.DataFrame({'Temp': [200.0]}) # Missing Grain Size
        ]
        result = accumulate_streaming_stats(iter(chunks), ['Temp', 'Grain Size'])
        
        assert result['columns']['Temp']['count'] == 2
        assert result['columns']['Grain Size']['count'] == 1

    def test_stats_match_full_load(self):
        """
        Verification: Confirm stats match a full-load calculation on a small test set.
        """
        # Generate a larger synthetic dataset to simulate a "real" load
        # Note: This is for unit testing logic, not the actual data ingestion which must use real sources.
        import numpy as np
        np.random.seed(42)
        n_rows = 1000
        full_data = pd.DataFrame({
            'Temp': np.random.uniform(400, 600, n_rows),
            'Grain Size': np.random.uniform(5, 25, n_rows)
        })
        
        # Split into chunks
        chunk_size = 100
        chunks = [full_data.iloc[i:i+chunk_size] for i in range(0, n_rows, chunk_size)]
        
        # Run streaming stats
        streaming_result = accumulate_streaming_stats(iter(chunks), ['Temp', 'Grain Size'])
        
        # Calculate full stats
        full_mean_temp = full_data['Temp'].mean()
        full_mean_grain = full_data['Grain Size'].mean()
        
        # Compare
        assert abs(streaming_result['columns']['Temp']['mean'] - full_mean_temp) < 1e-6
        assert abs(streaming_result['columns']['Grain Size']['mean'] - full_mean_grain) < 1e-6
        assert streaming_result['columns']['Temp']['count'] == n_rows

    def test_save_to_json(self, tmp_path):
        """
        Verify output is saved to data/artifacts/streaming_stats.json
        """
        df = pd.DataFrame({'Temp': [100.0, 200.0]})
        stats = accumulate_streaming_stats(iter([df]), ['Temp'])
        
        output_file = tmp_path / "streaming_stats.json"
        save_streaming_stats(stats, str(output_file))
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['total_rows'] == 2
        assert loaded['columns']['Temp']['mean'] == 150.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])