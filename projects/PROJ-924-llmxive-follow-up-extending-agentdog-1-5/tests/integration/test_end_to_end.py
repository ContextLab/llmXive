"""
Integration tests for the drift scoring pipeline, specifically focusing on
memory constraints during batch processing.
"""
import json
import os
import sys
import tracemalloc
import unittest
from pathlib import Path
from typing import List, Dict, Any

# Add the code directory to the path to allow imports
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import get_path, ensure_directories
from data_loader import fetch_advbench, fetch_hf4
from drift_scoring import batch_process_logs
from taxonomy_builder import load_taxonomy, build_centroids
from utils import load_json_file, save_json_file

# Memory limit in GB
MEMORY_LIMIT_GB = 4.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3

class TestBatchMemoryLimit(unittest.TestCase):
    """
    Integration test to verify that batch processing logs does not exceed
    the 4GB memory limit.
    """

    def setUp(self):
        """Set up test fixtures and ensure necessary directories exist."""
        ensure_directories()
        self.taxonomy_path = get_path("raw_taxonomy_json")
        self.centroids_path = get_path("taxonomy_centroids_json")
        
        # Ensure taxonomy and centroids are built before testing
        if not Path(self.taxonomy_path).exists():
            # If taxonomy doesn't exist, we assume T005d and T008a have run
            # For the test to run, we need these files. If they are missing,
            # the test will fail with a clear error, which is acceptable
            # as it indicates a prerequisite failure.
            raise FileNotFoundError(
                f"Taxonomy file not found at {self.taxonomy_path}. "
                "Please ensure T005d and T008a are completed."
            )

        if not Path(self.centroids_path).exists():
             raise FileNotFoundError(
                f"Centroids file not found at {self.centroids_path}. "
                "Please ensure T008a is completed."
            )

    def test_batch_memory_limit_4gb(self):
        """
        Test that processing a batch of logs does not exceed 4GB of RAM.
        
        This test:
        1. Loads a substantial number of logs from real datasets (AdvBench and HF4).
        2. Starts memory tracing.
        3. Runs the batch processing function.
        4. Stops memory tracing.
        5. Asserts that peak memory usage is below the 4GB limit.
        """
        # Load real data
        # Fetch a reasonable number of logs to stress test memory without
        # taking forever. We'll fetch 500 from each source.
        advbench_logs = fetch_advbench(num_samples=500)
        hf4_logs = fetch_hf4(num_samples=500)
        
        # Combine logs
        all_logs = []
        # Add IDs to distinguish sources and ensure uniqueness
        for i, log in enumerate(advbench_logs):
            log['log_id'] = f"advbench_{i}"
            all_logs.append(log)
        
        for i, log in enumerate(hf4_logs):
            log['log_id'] = f"hf4_{i}"
            all_logs.append(log)
        
        # Load centroids
        taxonomy_data = load_json_file(self.taxonomy_path)
        centroids = build_centroids(taxonomy_data)
        
        # Start memory tracing
        tracemalloc.start()
        
        try:
            # Run batch processing
            # Note: batch_process_logs expects centroids and a list of logs
            # It returns a list of results
            results = batch_process_logs(all_logs, centroids)
            
            # Stop tracing
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Assert peak memory is within limit
            peak_gb = peak / (1024**3)
            self.assertLess(
                peak_gb, 
                MEMORY_LIMIT_GB, 
                f"Peak memory usage {peak_gb:.2f} GB exceeds limit of {MEMORY_LIMIT_GB} GB"
            )
            
            # Verify that results were produced
            self.assertEqual(len(results), len(all_logs), 
                             "Number of results does not match number of input logs")
            
            # Verify result structure
            for result in results:
                self.assertIn('log_id', result)
                self.assertIn('drift_score', result)
                self.assertIn('review_flag', result)
                
        except Exception as e:
            tracemalloc.stop()
            self.fail(f"Batch processing failed with exception: {e}")

if __name__ == '__main__':
    unittest.main()