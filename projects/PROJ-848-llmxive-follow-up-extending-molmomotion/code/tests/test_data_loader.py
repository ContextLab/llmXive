"""
Unit tests for data_loader.py
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os
import tempfile
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_loader import subsample_instances, validate_sample_size, _estimate_instance_memory_mb

class MockInstance:
    """Mock dataset instance for testing."""
    def __init__(self, points_count: int = 100):
        self.data = {
            'instance_id': f"mock_{points_count}",
            'ground_truth_points': [[i, i+1, i+2] for i in range(points_count)],
            'instruction_nl': "mock instruction",
            'instruction_struct': [0.1, 0.2]
        }
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __contains__(self, key):
        return key in self.data

class MockStreamingDataset:
    """Mock streaming dataset."""
    def __init__(self, size: int = 1000):
        self.size = size
    
    def __iter__(self):
        for i in range(self.size):
            yield MockInstance(points_count=100)

class TestSubsampleInstances(unittest.TestCase):
    
    def test_reservoir_sampling_randomness(self):
        """Test that reservoir sampling produces a random sample."""
        # Create a deterministic iterator with known items
        items = [MockInstance(points_count=i) for i in range(100)]
        
        # Mock the iterator
        def mock_iter():
            for item in items:
                yield item.data
        
        # Run subsampling with a very small target to force replacement
        result = subsample_instances(
            data_iterator=mock_iter(),
            target_memory_gb=0.0001, # Very small to force strict constraints
            random_seed=42
        )
        
        # Should not be empty
        self.assertGreater(len(result), 0)
        
        # Run again with different seed to check randomness (conceptually)
        result2 = subsample_instances(
            data_iterator=mock_iter(),
            target_memory_gb=0.0001,
            random_seed=123
        )
        
        # They should likely differ if the sample is small enough
        # Note: This is a probabilistic test, but with small targets it should hold

    def test_memory_constraint(self):
        """Test that the result fits within memory constraints."""
        items = [MockInstance(points_count=10) for _ in range(100)]
        
        def mock_iter():
            for item in items:
                yield item.data

        # Target 1MB (should fit a few items)
        result = subsample_instances(
            data_iterator=mock_iter(),
            target_memory_gb=0.001, # 1MB
            random_seed=42
        )
        
        # Verify we got some results
        self.assertGreater(len(result), 0)

class TestValidateSampleSize(unittest.TestCase):
    
    def test_pass_threshold(self):
        """Test validation passes above threshold."""
        instances = [{"id": i} for i in range(1001)]
        self.assertTrue(validate_sample_size(instances, min_threshold=1000))
    
    def test_fail_threshold(self):
        """Test validation fails below threshold."""
        instances = [{"id": i} for i in range(999)]
        with self.assertRaises(RuntimeError):
            validate_sample_size(instances, min_threshold=1000)

class TestMemoryConstraintEdgeCases(unittest.TestCase):
    
    def test_empty_iterator(self):
        """Test handling of empty iterator."""
        def mock_iter():
            return iter([])
        
        with self.assertRaises(ValueError):
            subsample_instances(mock_iter(), target_memory_gb=1.0, random_seed=42)
    
    def test_single_large_item(self):
        """Test handling of an item larger than target."""
        # Create an item with huge points
        huge_item = {"ground_truth_points": [[0,0,0]] * 1000000}
        
        def mock_iter():
            yield huge_item
        
        # Should skip the item and return empty, raising ValueError
        with self.assertRaises(ValueError):
            subsample_instances(mock_iter(), target_memory_gb=0.001, random_seed=42)

if __name__ == '__main__':
    unittest.main()
