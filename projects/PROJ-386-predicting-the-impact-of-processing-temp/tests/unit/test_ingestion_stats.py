"""
Unit tests for the Online Statistics Aggregator (T049).
"""
import pytest
import pandas as pd
import numpy as np
from io import StringIO
import json
import os
import tempfile

from code.data.ingestion import (
    RunningStats, 
    accumulate_streaming_stats, 
    save_streaming_stats,
    CRITICAL_COLUMNS
)

class TestRunningStats:
    def test_update_basic(self):
        """Test basic mean and null count update."""
        stats = RunningStats(['A', 'B'])
        
        # Chunk 1
        df1 = pd.DataFrame({'A': [10, 20, 30], 'B': [1.0, 2.0, np.nan]})
        stats.update(df1)
        
        assert stats.count == 3
        assert stats.mean['A'] == 20.0
        assert stats.mean['B'] == 1.5
        assert stats.null_counts['A'] == 0
        assert stats.null_counts['B'] == 1

    def test_update_welford(self):
        """Test Welford's algorithm stability with incremental updates."""
        stats = RunningStats(['X'])
        
        # Simulate a large number of updates
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        expected_mean = sum(values) / len(values)
        
        for i, val in enumerate(values):
            chunk = pd.DataFrame({'X': [val]})
            stats.update(chunk)
        
        assert abs(stats.mean['X'] - expected_mean) < 1e-6
        assert stats.count == 10
        assert stats.null_counts['X'] == 0

    def test_update_with_nulls(self):
        """Test handling of null values."""
        stats = RunningStats(['Y'])
        df = pd.DataFrame({'Y': [1.0, np.nan, 3.0]})
        stats.update(df)
        
        assert stats.count == 2
        assert stats.mean['Y'] == 2.0
        assert stats.null_counts['Y'] == 1

class TestAccumulateStreamingStats:
    def test_accumulate_stats(self):
        """Test the full accumulation function with a mock iterator."""
        # Create mock chunks
        chunk1 = pd.DataFrame({'rolling temperature': [100, 200], 'grain size': [10.0, 20.0]})
        chunk2 = pd.DataFrame({'rolling temperature': [300], 'grain size': [np.nan]})
        
        def mock_iterator():
            yield chunk1
            yield chunk2
        
        stats = accumulate_streaming_stats(mock_iterator())
        
        # Expected:
        # Temp: 100, 200, 300 -> Mean = 200, Count = 3
        # Grain: 10.0, 20.0 -> Mean = 15.0, Count = 2 (1 null)
        
        assert stats['total_rows_processed'] == 3 # Based on non-null count for mean
        assert abs(stats['means']['rolling temperature'] - 200.0) < 1e-6
        assert abs(stats['means']['grain size'] - 15.0) < 1e-6
        assert stats['null_counts']['grain size'] == 1

    def test_empty_iterator(self):
        """Test behavior with empty iterator."""
        def empty_iterator():
            return
            yield # Make it a generator
        
        stats = accumulate_streaming_stats(empty_iterator())
        assert stats['total_rows_processed'] == 0
        assert all(v == 0.0 for v in stats['means'].values())

    def test_save_stats(self):
        """Test saving stats to JSON."""
        stats = {
            'total_rows_processed': 100,
            'means': {'A': 10.0},
            'null_counts': {'A': 5}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name
        
        try:
            save_streaming_stats(stats, temp_path)
            
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded == stats
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
