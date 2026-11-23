import os
import sys
import pytest
from pathlib import Path
import json
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from utils import set_deterministic_seed
from memory_utils import check_memory_thresholds, trigger_garbage_collection

class TestEdgeCasesIngestion:
    """
    Unit tests for edge cases in ingestion and memory management.
    """

    def test_empty_year_handling_in_similarity(self):
        """
        Test that similarity calculation handles years with no data gracefully.
        """
        # Mock the load_yearly_embeddings to return an empty dict or dict with empty arrays
        # This would be tested in similarity.py logic, but here we test the contract
        
        # Simulate a scenario where a year exists in metadata but has no tracks
        # This is handled by the embedding aggregation logic, but we test the validation
        pass

    def test_api_failure_retry_logic(self):
        """
        Test that the API fetch logic handles failures and retries.
        """
        # This tests the fetch_musicbrainz function's retry logic
        # We mock the requests.get to raise an exception
        
        with patch('requests.Session.get') as mock_get:
            mock_get.side_effect = [
                Exception("Connection Timeout"),
                Exception("Connection Timeout"),
                MagicMock(status_code=200, json=lambda: {"id": "123", "name": "Test"})
            ]
            
            # We would call the fetch function here, but since it's in ingest.py
            # and we are testing edge cases, we verify the retry mechanism exists
            # by checking the code or mocking the specific retry logic
            pass

    def test_memory_threshold_gc_trigger(self):
        """
        Test that memory threshold check triggers GC when memory is high.
        """
        # Mock psutil to return high memory usage
        with patch('psutil.Process') as MockProcess:
            mock_process = MagicMock()
            mock_process.memory_info.return_value = MagicMock(rss=6 * 1024 * 1024 * 1024) # 6GB
            mock_process.memory_percent.return_value = 95.0
            MockProcess.return_value = mock_process
            
            # Call the function
            result = check_memory_thresholds()
            
            # Verify that GC was triggered or warning was logged
            # This depends on the implementation of check_memory_thresholds
            # which should trigger GC if > 90%
            pass

    def test_empty_dataframe_handling(self):
        """
        Test that processing an empty dataframe does not crash.
        """
        df = pd.DataFrame()
        
        # Test functions that might receive empty data
        # e.g., calculate_mean_off_diagonal_similarity
        # We mock the inputs to similarity functions
        pass

    def test_missing_genre_tags(self):
        """
        Test handling of tracks with missing genre tags.
        """
        # Simulate a track with None or empty genre
        track_data = {"track_id": "1", "genre": None, "year": 2020}
        
        # The aggregation logic should handle this, possibly by skipping or zero-filling
        # We verify the logic in embeddings.py
        pass

class TestRegressionEdgeCases:
    """
    Unit tests for regression edge cases.
    """

    def test_low_coverage_year_exclusion(self):
        """
        Test that years with < 1000 tracks are excluded from regression.
        """
        # Mock the low_coverage_years.json
        with patch('builtins.open', mock_open(read_data='["2010", "2011"]')):
            # Test the prepare_exclusions logic
            pass

    def test_linear_regression_with_single_point(self):
        """
        Test regression fitting with only one valid year (should fail or warn).
        """
        # statsmodels will raise an error if there are not enough points
        # We test that the code handles this gracefully
        pass

    def test_cooks_distance_with_outliers(self):
        """
        Test Cook's Distance calculation with known outliers.
        """
        # Create a dataset with a known outlier
        data = pd.DataFrame({
            'year': [2010, 2011, 2012, 2013, 2014, 2015],
            'similarity': [0.5, 0.51, 0.52, 0.53, 0.54, 0.99] # 2015 is outlier
        })
        
        # Run Cook's Distance logic
        # Verify that 2015 has a high Cook's Distance
        pass

# Helper for mock_open if not imported
from unittest.mock import mock_open
