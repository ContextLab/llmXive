import os
import sys
import gc
import unittest
from unittest.mock import patch, MagicMock
import numpy as np

# Add code/ to path if not already
code_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'code')
if code_path not in sys.path:
    sys.path.insert(0, code_path)

from utils.memory_utils import (
    get_available_memory_gb,
    estimate_graph_memory,
    calculate_max_safe_sample_size,
    dynamic_sampling,
    verify_data_volume,
    enforce_memory_limit,
    get_memory_profile,
    MAX_MEMORY_GB,
    ESTIMATED_GRAPH_SIZE_GB
)

class MockGraph:
    """Mock graph object for testing."""
    def __init__(self, size_factor=1.0):
        self.size_factor = size_factor
        # Simulate some data that would consume memory
        self.node_features = np.random.rand(100, 10)
        self.edge_index = np.random.randint(0, 100, (2, 200))
        self.target = np.random.rand(3)

class TestMemoryUtils(unittest.TestCase):
    
    def test_get_available_memory_gb_linux(self):
        """Test memory reading on Linux."""
        # Mock /proc/meminfo
        mock_meminfo = "MemAvailable: 8000000 kB\n"
        with patch('builtins.open', unittest.mock.mock_open(read_data=mock_meminfo)):
            with patch('utils.memory_utils.sys.platform', 'linux'):
                result = get_available_memory_gb()
                # 8000000 kB = 8 GB
                self.assertAlmostEqual(result, 8.0, places=2)

    def test_get_available_memory_gb_default(self):
        """Test default memory limit on non-Linux."""
        with patch('utils.memory_utils.sys.platform', 'darwin'):
            result = get_available_memory_gb()
            self.assertEqual(result, MAX_MEMORY_GB)

    def test_estimate_graph_memory(self):
        """Test graph memory estimation."""
        graph = MockGraph()
        result = estimate_graph_memory(graph)
        self.assertEqual(result, ESTIMATED_GRAPH_SIZE_GB)

    def test_calculate_max_safe_sample_size(self):
        """Test calculation of max safe sample size."""
        # With 7GB limit and 0.8 safety factor, available = 5.6GB
        # At 0.01GB per graph, max = 560 graphs
        result = calculate_max_safe_sample_size(max_memory_gb=7.0, safety_factor=0.8)
        expected = int((7.0 * 0.8) / 0.01)
        self.assertEqual(result, expected)

    def test_dynamic_sampling_no_reduction(self):
        """Test dynamic sampling when no reduction needed."""
        graphs = [MockGraph() for _ in range(10)]
        result = dynamic_sampling(graphs, target_size=20)
        self.assertEqual(len(result), 10)
        self.assertIs(result, graphs)  # Should return same list

    def test_dynamic_sampling_reduction(self):
        """Test dynamic sampling when reduction needed."""
        graphs = [MockGraph() for _ in range(100)]
        result = dynamic_sampling(graphs, target_size=10, seed=42)
        self.assertEqual(len(result), 10)
        # Check that it's a subset
        for g in result:
            self.assertIn(g, graphs)

    def test_verify_data_volume_success(self):
        """Test data volume verification with enough data."""
        graphs = [MockGraph() for _ in range(150)]
        result = verify_data_volume(graphs, min_required=100)
        self.assertTrue(result)

    def test_verify_data_volume_failure(self):
        """Test data volume verification with insufficient data."""
        graphs = [MockGraph() for _ in range(50)]
        result = verify_data_volume(graphs, min_required=100)
        self.assertFalse(result)

    def test_get_memory_profile(self):
        """Test memory profile generation."""
        profile = get_memory_profile()
        self.assertIn('available_gb', profile)
        self.assertIn('estimated_per_graph_gb', profile)
        self.assertIn('max_safe_sample_size', profile)
        self.assertIsInstance(profile['available_gb'], float)
        self.assertIsInstance(profile['estimated_per_graph_gb'], float)
        self.assertIsInstance(profile['max_safe_sample_size'], int)

    def test_enforce_memory_limit_success(self):
        """Test callback execution within memory limit."""
        def dummy_callback():
            return "success"
        
        peak_tracker = []
        def track_peak(peak_gb):
            peak_tracker.append(peak_gb)
        
        result = enforce_memory_limit(
            dummy_callback, 
            peak_memory_callback=track_peak
        )
        
        self.assertEqual(result, "success")
        self.assertEqual(len(peak_tracker), 1)
        self.assertLess(peak_tracker[0], MAX_MEMORY_GB)

    def test_enforce_memory_limit_exceeded(self):
        """Test memory limit enforcement when exceeded."""
        # Mock tracemalloc to report high memory
        def dummy_callback():
            return "should not reach"
        
        with patch('utils.memory_utils.tracemalloc.get_traced_memory', return_value=(0, int(MAX_MEMORY_GB * 1.5 * 1024 * 1024 * 1024))):
            with self.assertRaises(MemoryError):
                enforce_memory_limit(dummy_callback)

    def test_full_pipeline_memory_simulation(self):
        """
        Simulate the entire data loading and training loop to verify memory usage < 7GB.
        
        This test creates a realistic scenario where:
        1. We load a large number of graphs
        2. We perform sampling to fit in memory
        3. We simulate a training loop with memory monitoring
        4. We assert that peak memory stays under 7GB
        """
        # Step 1: Generate a large set of mock graphs (simulating raw data)
        num_total_graphs = 1000
        all_graphs = [MockGraph() for _ in range(num_total_graphs)]
        
        # Step 2: Calculate safe sample size
        safe_size = calculate_max_safe_sample_size(max_memory_gb=MAX_MEMORY_GB, safety_factor=SAFETY_FACTOR)
        
        # Step 3: Apply dynamic sampling
        sampled_graphs = dynamic_sampling(all_graphs, target_size=safe_size, seed=42)
        
        # Verify we have enough data
        self.assertTrue(verify_data_volume(sampled_graphs, min_required=100), 
                       "Sampled data volume insufficient for training")
        
        # Step 4: Simulate training loop with memory monitoring
        peak_memory_log = []
        
        def simulate_training_epoch(graph_batch):
            """Simulate one epoch of training on a batch of graphs."""
            # Simulate processing (e.g., converting to tensors, forward pass)
            for g in graph_batch:
                # Simulate some computation that uses memory
                _ = g.node_features @ g.node_features.T
                _ = g.edge_index.sum()
            return 0.5  # dummy loss
        
        def full_pipeline():
            """Simulate the full pipeline: load -> sample -> train."""
            for i in range(5):  # 5 epochs
                # Simulate batching
                batch_size = 32
                for start in range(0, len(sampled_graphs), batch_size):
                    batch = sampled_graphs[start:start+batch_size]
                    loss = simulate_training_epoch(batch)
                # Simulate checkpoint saving (clears some memory)
                gc.collect()
            return "training_complete"
        
        # Run the pipeline with memory enforcement
        result = enforce_memory_limit(
            full_pipeline,
            peak_memory_callback=lambda peak_gb: peak_memory_log.append(peak_gb)
        )
        
        self.assertEqual(result, "training_complete")
        self.assertTrue(len(peak_memory_log) > 0, "No peak memory recorded")
        
        # Assert that peak memory stayed under 7GB
        max_peak = max(peak_memory_log)
        self.assertLess(
            max_peak, 
            MAX_MEMORY_GB, 
            f"Peak memory {max_peak:.2f}GB exceeded limit of {MAX_MEMORY_GB}GB"
        )
        
        print(f"Full pipeline simulation successful. Peak memory: {max_peak:.2f}GB")

if __name__ == '__main__':
    unittest.main()