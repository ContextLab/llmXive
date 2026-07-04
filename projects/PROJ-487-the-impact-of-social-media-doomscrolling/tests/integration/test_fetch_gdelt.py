"""
Integration test verifying non-empty CSV generation for GDELT.
This test will attempt to fetch real data. If the API is unreachable, it should fail clearly.
"""
import unittest
import os
import sys
from pathlib import Path
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from fetch_data import fetch_gdelt_sentiment

class TestFetchGdeltIntegration(unittest.TestCase):

    def test_gdelt_csv_generation(self):
        """Test that fetch_gdelt_sentiment creates a non-empty CSV."""
        output_path = "/tmp/test_gdelt_integration.csv"
        
        # Use a very recent date range to minimize API issues
        # GDELT might not have data for the future, so use past dates
        # Let's try a range that is likely to have data
        start_date = "20230101"
        end_date = "20230102"
        
        success = fetch_gdelt_sentiment(
            start_date=start_date,
            end_date=end_date,
            output_path=output_path,
            max_retries=3,
            rate_limit_wait=1.0,
            backoff_factor=1.0
        )
        
        # Even if the API returns no events, the file should exist
        # The task says "verify the output CSV files ... contain non-empty rows"
        # If the API is down, this test will fail, which is expected behavior for integration tests
        # against external services.
        
        self.assertTrue(success, "Fetch should return True (even if no data found)")
        self.assertTrue(Path(output_path).exists(), "Output CSV should exist")
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            # The task requires non-empty rows for the target date range.
            # If the API returns no data for the specific range, this will fail.
            # However, for the purpose of the test, we check if the file was created.
            # If the API is working and returns data, rows should not be empty.
            # We'll assert that rows are not empty to satisfy the task requirement.
            # If the API is down, this test will fail, which is acceptable for an integration test
            # that depends on an external service.
            # But to be safe, we might want to check if the API is reachable first.
            # For now, we assume the API is reachable.
            self.assertGreater(len(rows), 0, "CSV should contain at least one row")

if __name__ == '__main__':
    unittest.main()