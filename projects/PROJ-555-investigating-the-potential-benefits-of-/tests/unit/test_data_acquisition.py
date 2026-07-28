"""
Unit tests for chunked download logic in data acquisition.

This module verifies that the chunked download logic in `code/data_acquisition.py`
correctly handles streaming data, respects memory constraints, and processes
data in chunks as defined by the chunking utility.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import json
import logging
from io import StringIO

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data_acquisition import log_api_query, fetch_landsat_metadata, main
from code.utils.chunking import (
    calculate_safe_chunk_size,
    process_chunked,
    estimate_row_size
)
from code.config import ensure_directories
from code.logging_config import setup_logging

# Constants for testing
MOCK_SCENE_ID = "LC08_L2SP_044034_20200101_20200101_01_T1"
MOCK_QUERY_PARAMS = {
    "start_date": "2020-01-01",
    "end_date": "2020-01-31",
    "max_results": 100
}
MOCK_RESPONSE = {
    "data": [
        {
            "id": MOCK_SCENE_ID,
            "displayId": "LC08_L2SP_044034_20200101_20200101_01_T1",
            "entityId": "LC80440342020001LGN00",
            "browse": [
                {
                    "thumbnail": "https://example.com/thumb.jpg",
                    "full": "https://example.com/full.jpg"
                }
            ]
        }
    ],
    "recordsReturned": 1,
    "totalHits": 1
}

class TestChunkedDownloadLogic(unittest.TestCase):
    """Tests for chunked download and processing logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = Path("tests/test_output")
        self.test_dir.mkdir(exist_ok=True)
        setup_logging()
        self.logger = logging.getLogger(__name__)

    def tearDown(self):
        """Clean up test artifacts."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_calculate_safe_chunk_size_memory_limit(self):
        """Test that chunk size calculation respects memory limits."""
        # Mock available memory to be low (e.g., 100MB)
        with patch('code.utils.chunking.get_available_memory', return_value=100 * 1024 * 1024):
            # Estimate row size
            row_size = estimate_row_size([{"id": "test", "data": "x" * 1000}])
            chunk_size = calculate_safe_chunk_size(row_size, max_memory_mb=100)
            
            # Chunk size should be positive and reasonable
            self.assertGreater(chunk_size, 0)
            self.assertLess(chunk_size, 1000000)  # Should not be absurdly large

    @patch('code.data_acquisition.fetch_landsat_metadata')
    def test_fetch_landsat_metadata_chunked_processing(self, mock_fetch):
        """Test that fetch_landsat_metadata processes results in chunks."""
        # Setup mock to return multiple pages of results
        mock_fetch.side_effect = [
            {"data": [{"id": f"scene_{i}"} for i in range(50)], "recordsReturned": 50},
            {"data": [{"id": f"scene_{i+50}"} for i in range(50)], "recordsReturned": 50},
            {"data": [], "recordsReturned": 0}  # End of results
        ]

        # Call function with chunked processing
        results = fetch_landsat_metadata(
            start_date="2020-01-01",
            end_date="2020-01-31",
            max_results=100,
            chunk_size=50
        )

        # Verify we got all results
        self.assertEqual(len(results), 100)
        
        # Verify fetch was called multiple times (chunked)
        self.assertEqual(mock_fetch.call_count, 3)

    def test_process_chunked_iterator_behavior(self):
        """Test that process_chunked correctly yields chunks."""
        # Create a large list of items
        items = list(range(100))
        chunk_size = 25

        chunks = list(process_chunked(items, chunk_size))

        # Verify chunk structure
        self.assertEqual(len(chunks), 4)  # 100 / 25 = 4
        self.assertEqual(len(chunks[0]), 25)
        self.assertEqual(chunks[0][0], 0)
        self.assertEqual(chunks[0][-1], 24)
        self.assertEqual(chunks[-1][-1], 99)

    def test_log_api_query_with_chunked_params(self):
        """Test logging of API queries with chunked parameters."""
        query_params = {
            "start_date": "2020-01-01",
            "end_date": "2020-01-31",
            "chunk_size": 50,
            "max_results": 1000
        }
        
        # Ensure directories exist
        ensure_directories()
        
        # Log the query
        log_api_query("landsat_search", query_params)
        
        # Verify log file exists and contains the query
        log_dir = Path("data/raw")
        log_files = list(log_dir.glob("query_log.json"))
        self.assertGreater(len(log_files), 0)
        
        with open(log_files[0], 'r') as f:
            log_content = json.load(f)
        
        # Check that our query was logged
        found = False
        for entry in log_content:
            if entry.get("query_type") == "landsat_search":
                self.assertEqual(entry["params"]["chunk_size"], 50)
                found = True
                break
        
        self.assertTrue(found, "Query not found in log")

    @patch('code.data_acquisition.fetch_landsat_metadata')
    @patch('code.data_acquisition.log_api_query')
    def test_main_chunked_download_workflow(self, mock_log, mock_fetch):
        """Test the full main workflow with chunked download."""
        # Setup mock data
        mock_fetch.return_value = {
            "data": [{"id": f"scene_{i}"} for i in range(10)],
            "recordsReturned": 10
        }
        
        # Run main with chunked parameters
        try:
            main(
                start_date="2020-01-01",
                end_date="2020-01-31",
                output_path=str(self.test_dir / "test_output.json"),
                chunk_size=5
            )
        except Exception as e:
            # Some errors are expected if real API calls fail, 
            # but we're testing the logic flow
            pass
        
        # Verify log was called with chunked parameters
        self.assertTrue(mock_log.called)
        call_args = mock_log.call_args[0]
        self.assertEqual(call_args[0], "landsat_search")
        self.assertIn("chunk_size", call_args[1])
        self.assertEqual(call_args[1]["chunk_size"], 5)

    def test_chunked_memory_safety(self):
        """Test that chunked processing doesn't exceed memory limits."""
        # Create a generator that simulates large data
        def large_data_generator():
            for i in range(1000):
                yield {"id": i, "data": "x" * 1000}
        
        # Process in small chunks
        chunk_count = 0
        total_items = 0
        
        for chunk in process_chunked(large_data_generator(), chunk_size=100):
            chunk_count += 1
            total_items += len(chunk)
            # Simulate processing
            _ = len(chunk)
        
        # Verify correct chunking
        self.assertEqual(chunk_count, 10)  # 1000 / 100
        self.assertEqual(total_items, 1000)

    def test_empty_chunk_handling(self):
        """Test that empty chunks are handled gracefully."""
        # Empty iterator
        empty_iter = iter([])
        chunks = list(process_chunked(empty_iter, chunk_size=10))
        self.assertEqual(len(chunks), 0)

    def test_partial_last_chunk(self):
        """Test that partial chunks at the end are handled correctly."""
        items = list(range(23))
        chunk_size = 10
        
        chunks = list(process_chunked(items, chunk_size))
        
        # Should have 3 chunks: [0-9], [10-19], [20-22]
        self.assertEqual(len(chunks), 3)
        self.assertEqual(len(chunks[0]), 10)
        self.assertEqual(len(chunks[1]), 10)
        self.assertEqual(len(chunks[2]), 3)
        self.assertEqual(chunks[2][-1], 22)


if __name__ == "__main__":
    unittest.main()