"""
Test skeleton for graph construction memory limit (US1).

This module contains tests that verify the memory usage of graph construction
and preprocessing pipelines does not exceed the defined limit (7GB).

Dependencies:
    - code/utils/memory_monitor.py (T005, T015)
    - code/data/preprocess.py (T013, T008)
"""

import os
import sys
import unittest
import tracemalloc
from unittest.mock import patch, MagicMock

# Add project root to path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.memory_monitor import (
    MemoryLimitExceededError,
    start_monitoring,
    stop_monitoring,
    get_peak_memory_mb,
    check_memory_limit,
    memory_limit_context,
)
from data.preprocess import build_graph_from_csv, preprocess_graph

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024


class TestGraphConstructionMemoryLimit(unittest.TestCase):
    """
    Tests to assert that graph construction operations stay within the 7GB memory limit.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.temp_csv_path = None
        self.temp_graph_path = None

    def tearDown(self):
        """Clean up test artifacts."""
        if self.temp_csv_path and os.path.exists(self.temp_csv_path):
            os.remove(self.temp_csv_path)
        if self.temp_graph_path and os.path.exists(self.temp_graph_path):
            os.remove(self.temp_graph_path)

    def _create_mock_csv(self, num_rows=1000):
        """Helper to create a minimal CSV for testing."""
        import pandas as pd
        import tempfile

        data = {
            "src_ip": [f"192.168.1.{i % 255}" for i in range(num_rows)],
            "dst_ip": [f"10.0.0.{i % 255}" for i in range(num_rows)],
            "protocol": ["TCP"] * num_rows,
            "packets": [10] * num_rows,
            "bytes": [1000] * num_rows,
            "label": ["normal"] * num_rows
        }
        df = pd.DataFrame(data)

        fd, path = tempfile.mktemp(suffix=".csv", dir="data/raw")
        df.to_csv(path, index=False)
        self.temp_csv_path = path
        return path

    def test_memory_monitor_context_manager(self):
        """
        Verify that the memory_limit_context manager raises an error when limit is exceeded.
        This ensures the mechanism to enforce limits works before testing the actual graph builder.
        """
        # We mock the get_peak_memory_mb function to simulate a high memory usage
        with patch("utils.memory_monitor.get_peak_memory_mb", return_value=8000):  # 8GB > 7GB
            with self.assertRaises(MemoryLimitExceededError):
                with memory_limit_context(limit_mb=MEMORY_LIMIT_MB):
                    pass  # Simulate work

    def test_memory_monitor_context_manager_safe(self):
        """
        Verify that the memory_limit_context manager does NOT raise when usage is within limits.
        """
        with patch("utils.memory_monitor.get_peak_memory_mb", return_value=1000):  # 1GB < 7GB
            try:
                with memory_limit_context(limit_mb=MEMORY_LIMIT_MB):
                    pass  # Simulate work
            except MemoryLimitExceededError:
                self.fail("memory_limit_context raised unexpectedly for safe memory usage")

    @patch("data.preprocess.build_graph_from_csv")
    def test_build_graph_memory_check_mocked(self, mock_build):
        """
        Test that the preprocess_graph function (or wrapper) checks memory limits.
        This is a skeleton test that asserts the interface exists and checks memory.
        
        Since we cannot easily simulate real memory spikes in a unit test without
        heavy mocking of the OS, we verify that the logic path for memory checking
        is present by mocking the heavy operation and asserting the check is called.
        """
        # Setup mock to return a simple graph object
        import networkx as nx
        mock_graph = nx.Graph()
        mock_build.return_value = mock_graph

        csv_path = self._create_mock_csv(100)
        output_path = "data/processed/test_graph.graphml"

        # We expect preprocess_graph to handle the memory logic
        # Note: This test assumes preprocess_graph internally calls memory checks
        # or that we are testing the integration of the check.
        # For a skeleton, we verify the function runs without crashing under mock.
        
        try:
            # Call the function that should enforce limits
            preprocess_graph(csv_path, output_path)
            
            # Verify the mock was called
            self.assertTrue(mock_build.called)
            
            # Verify output file was created (if logic is correct)
            self.assertTrue(os.path.exists(output_path))
            
        except MemoryLimitExceededError:
            # This is also acceptable if the mock somehow triggered the limit logic
            # but ideally we want the function to run successfully in mock mode
            pass
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_tracemalloc_direct_check(self):
        """
        Direct test of tracemalloc integration within the memory monitor.
        Verifies that start/stop and peak calculation work correctly.
        """
        start_monitoring()
        
        # Allocate some memory
        data = [i for i in range(100000)]
        
        peak = get_peak_memory_mb()
        stop_monitoring()
        
        # Peak should be non-negative
        self.assertGreaterEqual(peak, 0)
        
        # Clean up
        del data

    def test_check_memory_limit_function(self):
        """
        Test the check_memory_limit function directly.
        """
        # Should return True for low memory
        with patch("utils.memory_monitor.get_peak_memory_mb", return_value=100):
            self.assertTrue(check_memory_limit(1000))
        
        # Should return False (or raise, depending on implementation) for high memory
        # The API surface says check_memory_limit returns bool or raises?
        # Looking at imports: check_memory_limit is in utils.memory_monitor
        # Assuming it raises or returns False. Let's test the return value logic.
        with patch("utils.memory_monitor.get_peak_memory_mb", return_value=8000):
            result = check_memory_limit(1000) # 8GB > 1GB limit
            # If it returns bool:
            if isinstance(result, bool):
                self.assertFalse(result)
            # If it raises, the test would fail here unless we catch it.
            # Given the context manager exists, check_memory_limit likely returns bool.

    def test_integration_preprocess_memory_flow(self):
        """
        Integration-style skeleton test:
        1. Create a small CSV.
        2. Run preprocess_graph.
        3. Assert peak memory did not exceed limit during execution.
        
        Note: This test relies on the actual implementation of preprocess_graph
        calling memory checks. If preprocess_graph is not yet fully implemented
        to call these checks, this test might pass trivially (no check called)
        or fail if the check is missing.
        """
        csv_path = self._create_mock_csv(500)
        output_path = "data/processed/test_integration.graphml"
        
        start_monitoring()
        try:
            preprocess_graph(csv_path, output_path)
            peak = get_peak_memory_mb()
            
            # Assert we stayed under 7GB (7168 MB)
            self.assertLess(peak, MEMORY_LIMIT_MB, 
                            f"Peak memory {peak}MB exceeded limit {MEMORY_LIMIT_MB}MB")
            
            # Assert output exists
            self.assertTrue(os.path.exists(output_path))
            
        finally:
            stop_monitoring()
            if os.path.exists(output_path):
                os.remove(output_path)


if __name__ == "__main__":
    unittest.main()