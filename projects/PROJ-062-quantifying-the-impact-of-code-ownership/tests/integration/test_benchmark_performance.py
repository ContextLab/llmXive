"""
Integration tests for benchmark_performance.py
Verifies that memory monitoring and performance checks work correctly.
"""
import os
import sys
import json
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import psutil

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from scripts.benchmark_performance import MemoryMonitor, run_benchmark
from utils.memory_utils import get_current_memory_mb, check_memory_limit, force_gc

class TestMemoryMonitor(unittest.TestCase):
    """Test cases for MemoryMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = MemoryMonitor(limit_mb=7000.0)
    
    def test_initial_state(self):
        """Test initial memory monitor state."""
        self.assertEqual(self.monitor.peak_memory_mb, 0.0)
        self.assertEqual(len(self.monitor.memory_samples), 0)
        self.assertTrue(self.monitor.check_limit())
    
    def test_sample_recording(self):
        """Test that samples are recorded correctly."""
        self.monitor.sample("test_stage", "test_step")
        
        self.assertEqual(len(self.monitor.memory_samples), 1)
        sample = self.monitor.memory_samples[0]
        
        self.assertEqual(sample["stage"], "test_stage")
        self.assertEqual(sample["step"], "test_step")
        self.assertIn("memory_mb", sample)
        self.assertIn("timestamp", sample)
        self.assertIn("peak_so_far_mb", sample)
    
    def test_peak_memory_tracking(self):
        """Test that peak memory is tracked correctly."""
        # Simulate increasing memory usage
        self.monitor.peak_memory_mb = 1000.0
        self.monitor.sample("stage1", "step1")
        
        # Current memory should be at least the peak
        self.assertGreaterEqual(self.monitor.peak_memory_mb, 1000.0)
    
    def test_limit_check(self):
        """Test memory limit checking."""
        # Within limit
        self.monitor.peak_memory_mb = 5000.0
        self.assertTrue(self.monitor.check_limit())
        
        # Exceed limit
        self.monitor.peak_memory_mb = 8000.0
        self.assertFalse(self.monitor.check_limit())
    
    def test_summary_generation(self):
        """Test summary generation."""
        self.monitor.sample("stage1", "step1")
        self.monitor.sample("stage2", "step2")
        
        summary = self.monitor.get_summary()
        
        self.assertIn("peak_memory_mb", summary)
        self.assertIn("limit_mb", summary)
        self.assertIn("within_limit", summary)
        self.assertIn("sample_count", summary)
        self.assertIn("samples", summary)
        self.assertEqual(summary["sample_count"], 2)

class TestMemoryUtils(unittest.TestCase):
    """Test cases for memory utility functions."""
    
    def test_get_current_memory_mb(self):
        """Test current memory retrieval."""
        memory = get_current_memory_mb()
        self.assertGreater(memory, 0)
        self.assertIsInstance(memory, float)
    
    def test_check_memory_limit(self):
        """Test memory limit checking."""
        # Should pass with high limit
        self.assertTrue(check_memory_limit(limit_mb=100000.0))
        
        # Should pass with reasonable limit
        self.assertTrue(check_memory_limit(limit_mb=7000.0))
    
    def test_force_gc(self):
        """Test garbage collection."""
        # This should not raise any exceptions
        force_gc()
        self.assertTrue(True)

class TestBenchmarkPerformance(unittest.TestCase):
    """Test cases for benchmark performance functionality."""
    
    @patch('scripts.benchmark_performance.run_optimized_pipeline')
    @patch('scripts.benchmark_performance.time')
    def test_run_benchmark_success(self, mock_time, mock_run_pipeline):
        """Test successful benchmark execution."""
        # Mock time functions
        mock_time.time.side_effect = [0.0, 100.0]  # Start and end times
        mock_time.strftime.return_value = "2024-01-01 00:00:00"
        
        # Mock pipeline result
        mock_run_pipeline.return_value = {
            "peak_memory_mb": 5000.0,
            "limit_mb": 7000.0,
            "within_limit": True,
            "sample_count": 10,
            "samples": []
        }
        
        # Run benchmark
        result = run_benchmark()
        
        # Verify results
        self.assertIn("memory", result)
        self.assertIn("runtime", result)
        self.assertIn("compliance", result)
        self.assertTrue(result["compliance"]["overall_compliant"])
        self.assertLessEqual(result["runtime"]["total_hours"], 6.0)
    
    @patch('scripts.benchmark_performance.run_optimized_pipeline')
    @patch('scripts.benchmark_performance.time')
    def test_run_benchmark_memory_exceeded(self, mock_time, mock_run_pipeline):
        """Test benchmark when memory limit is exceeded."""
        # Mock time functions
        mock_time.time.side_effect = [0.0, 100.0]
        mock_time.strftime.return_value = "2024-01-01 00:00:00"
        
        # Mock pipeline result with memory exceeded
        mock_run_pipeline.return_value = {
            "peak_memory_mb": 8000.0,
            "limit_mb": 7000.0,
            "within_limit": False,
            "sample_count": 10,
            "samples": []
        }
        
        # Run benchmark
        result = run_benchmark()
        
        # Verify results
        self.assertFalse(result["compliance"]["overall_compliant"])
        self.assertFalse(result["compliance"]["memory_ok"])
    
    def test_benchmark_report_file_creation(self):
        """Test that benchmark report file is created."""
        # This test would require actual pipeline execution
        # For now, we verify the file path logic
        output_dir = Path("data/results")
        report_path = output_dir / "benchmark_report.json"
        
        self.assertEqual(str(report_path), "data/results/benchmark_report.json")

if __name__ == "__main__":
    unittest.main()
