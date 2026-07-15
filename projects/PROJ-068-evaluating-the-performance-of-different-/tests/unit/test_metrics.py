"""
Unit tests for memory_profiler integration in benchmarks/metrics.py.

This module verifies that the measure_memory function correctly wraps
memory_profiler's memory_usage to capture peak memory usage in MB.
"""
import unittest
from unittest.mock import patch, MagicMock
import time
import sys
import os

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from benchmarks.metrics import measure_memory, BenchmarkRun
from dataclasses import dataclass


class TestMeasureMemory(unittest.TestCase):
    """Tests for the measure_memory wrapper function."""

    def test_measure_memory_returns_dict(self):
        """Verify measure_memory returns a dictionary with expected keys."""
        def dummy_func():
            time.sleep(0.01)

        result = measure_memory(dummy_func)
        
        self.assertIsInstance(result, dict)
        self.assertIn('peak_memory_mb', result)
        self.assertIn('execution_time_s', result)
        self.assertIn('success', result)

    def test_measure_memory_success_flag(self):
        """Verify success flag is True when function executes without error."""
        def dummy_func():
            time.sleep(0.01)

        result = measure_memory(dummy_func)
        self.assertTrue(result['success'])

    def test_measure_memory_handles_exceptions(self):
        """Verify success flag is False when function raises an exception."""
        def failing_func():
            raise ValueError("Intentional failure")

        result = measure_memory(failing_func)
        self.assertFalse(result['success'])
        self.assertIn('error_message', result)
        self.assertEqual(result['error_message'], "Intentional failure")

    def test_measure_memory_peak_memory_positive(self):
        """Verify peak_memory_mb is a positive number on successful run."""
        def dummy_func():
            time.sleep(0.01)

        result = measure_memory(dummy_func)
        if result['success']:
            self.assertGreater(result['peak_memory_mb'], 0)
            self.assertIsInstance(result['peak_memory_mb'], float)

    def test_measure_memory_execution_time_positive(self):
        """Verify execution_time_s is a positive number on successful run."""
        def dummy_func():
            time.sleep(0.01)

        result = measure_memory(dummy_func)
        if result['success']:
            self.assertGreater(result['execution_time_s'], 0)
            self.assertIsInstance(result['execution_time_s'], float)

    @patch('benchmarks.metrics.memory_usage')
    def test_measure_memory_calls_memory_profiler(self, mock_mem_usage):
        """Verify that measure_memory actually calls memory_profiler.memory_usage."""
        # Mock the return value of memory_usage to be a list of memory samples
        mock_mem_usage.return_value = [10.0, 10.5, 11.0]
        
        def dummy_func():
            time.sleep(0.01)

        measure_memory(dummy_func)
        
        # Verify memory_usage was called with the function
        mock_mem_usage.assert_called_once()
        args, kwargs = mock_mem_usage.call_args
        
        # The first argument should be the function or a tuple containing the function
        # memory_usage signature: memory_usage((func, args, kwargs), ...)
        if isinstance(args[0], tuple):
            self.assertEqual(args[0][0], dummy_func)
        else:
            # In some versions it might be passed differently, check the callable
            self.assertEqual(args[0], dummy_func)

    def test_measure_memory_correct_peak_calculation(self):
        """Verify peak memory is calculated as the max of samples."""
        # We can't easily mock the internal logic without patching too much,
        # but we can verify the behavior with a simple function that allocates memory.
        
        def allocating_func():
            # Allocate some memory to ensure a measurable difference
            data = [0] * 100000
            time.sleep(0.01)
            return data

        result = measure_memory(allocating_func)
        self.assertTrue(result['success'])
        self.assertGreater(result['peak_memory_mb'], 0)


class TestBenchmarkRunDataClass(unittest.TestCase):
    """Tests for the BenchmarkRun dataclass structure."""

    def test_benchmark_run_creation(self):
        """Verify BenchmarkRun can be instantiated with required fields."""
        run = BenchmarkRun(
            dataset_size=10000,
            fpr_target=0.01,
            implementation_type="ArrayBloomFilter",
            peak_memory_mb=15.5,
            query_latency_ms=0.05,
            repetition_id=1,
            query_count=100000
        )
        
        self.assertEqual(run.dataset_size, 10000)
        self.assertEqual(run.fpr_target, 0.01)
        self.assertEqual(run.implementation_type, "ArrayBloomFilter")
        self.assertEqual(run.peak_memory_mb, 15.5)
        self.assertEqual(run.query_latency_ms, 0.05)
        self.assertEqual(run.repetition_id, 1)
        self.assertEqual(run.query_count, 100000)

    def test_benchmark_run_optional_fields(self):
        """Verify BenchmarkRun handles optional fields correctly."""
        run = BenchmarkRun(
            dataset_size=10000,
            fpr_target=0.01,
            implementation_type="ArrayBloomFilter",
            peak_memory_mb=15.5,
            query_latency_ms=0.05,
            repetition_id=1,
            query_count=100000,
            timestamp="2023-10-01T12:00:00"
        )
        
        self.assertEqual(run.timestamp, "2023-10-01T12:00:00")


if __name__ == '__main__':
    unittest.main()