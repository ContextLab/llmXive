"""
Unit tests for performance optimization components.

These tests verify that the optimization guide correctly:
1. Applies performance optimizations
2. Monitors pipeline performance
3. Generates accurate performance reports
"""
import os
import sys
import json
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.optimization_guide import (
    PerformanceMonitor,
    optimize_dataset_loading,
    optimize_feature_extraction,
    optimize_model_training,
    apply_all_optimizations
)


class TestPerformanceMonitor(unittest.TestCase):
    """Test cases for PerformanceMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.temp_dir, "test_performance.json")
        self.monitor = PerformanceMonitor(self.output_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_start_monitoring(self):
        """Test that monitoring starts correctly."""
        self.assertIsNone(self.monitor.start_time)
        self.monitor.start()
        self.assertIsNotNone(self.monitor.start_time)
        self.assertIn("optimizations_applied", self.monitor.metrics)
    
    def test_record_stage(self):
        """Test stage timing recording."""
        self.monitor.start()
        time.sleep(0.1)  # Small delay to ensure measurable time
        self.monitor.record_stage("test_stage", 0.1)
        
        self.assertIn("test_stage", self.monitor.metrics["stage_timings"])
        self.assertGreater(self.monitor.metrics["stage_timings"]["test_stage"]["duration_seconds"], 0)
    
    def test_update_memory(self):
        """Test memory usage tracking."""
        self.monitor.update_memory()
        # Should not raise an exception
        self.assertIsInstance(self.monitor.metrics["peak_memory_mb"], (int, float))
    
    def test_save_report(self):
        """Test performance report saving."""
        self.monitor.start()
        self.monitor.record_stage("test", 0.01)
        self.monitor.save_report()
        
        self.assertTrue(os.path.exists(self.output_path))
        
        with open(self.output_path, 'r') as f:
            report = json.load(f)
        
        self.assertIn("total_runtime_seconds", report)
        self.assertIn("stage_timings", report)
        self.assertIn("optimizations_applied", report)
    
    def test_total_runtime_calculation(self):
        """Test that total runtime is calculated correctly."""
        self.monitor.start()
        time.sleep(0.1)
        self.monitor.save_report()
        
        self.assertGreater(self.monitor.metrics["total_runtime_seconds"], 0)
        self.assertLess(self.monitor.metrics["total_runtime_seconds"], 1)  # Should be < 1 second


class TestOptimizationFunctions(unittest.TestCase):
    """Test cases for optimization functions."""
    
    @patch('scripts.optimization_guide.get_config')
    def test_optimize_dataset_loading(self, mock_get_config):
        """Test dataset loading optimization."""
        mock_config = MagicMock()
        mock_config.data_path = "/tmp/test"
        mock_get_config.return_value = mock_config
        
        # Should not raise an exception
        optimize_dataset_loading()
        
        # Verify environment variables were set
        self.assertIn('HUGGINGFACE_DATASETS_CACHE', os.environ)
    
    def test_optimize_feature_extraction(self):
        """Test feature extraction optimization."""
        # Should not raise an exception
        optimize_feature_extraction()
        # This is mainly a logging function, so we just verify it runs
    
    @patch('scripts.optimization_guide.os')
    def test_optimize_model_training(self, mock_os):
        """Test model training optimization."""
        optimize_model_training()
        
        # Verify CPU optimization environment variables were set
        mock_os.environ.__setitem__.assert_any_call('OPENBLAS_NUM_THREADS', '1')
        mock_os.environ.__setitem__.assert_any_call('MKL_NUM_THREADS', '1')
    
    @patch('scripts.optimization_guide.optimize_dataset_loading')
    @patch('scripts.optimization_guide.optimize_feature_extraction')
    @patch('scripts.optimization_guide.optimize_model_training')
    def test_apply_all_optimizations(self, mock_opt_model, mock_opt_feature, mock_opt_dataset):
        """Test that all optimizations are applied."""
        apply_all_optimizations()
        
        mock_opt_dataset.assert_called_once()
        mock_opt_feature.assert_called_once()
        mock_opt_model.assert_called_once()


class TestPerformanceOptimizationIntegration(unittest.TestCase):
    """Integration tests for performance optimization."""
    
    def test_performance_monitor_context(self):
        """Test performance monitoring in a realistic context."""
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "integration_test.json")
        
        try:
            monitor = PerformanceMonitor(output_path)
            monitor.start()
            
            # Simulate some work
            time.sleep(0.05)
            monitor.record_stage("simulated_work", 0.05)
            monitor.update_memory()
            
            monitor.save_report()
            
            # Verify the report
            with open(output_path, 'r') as f:
                report = json.load(f)
            
            self.assertGreater(report["total_runtime_seconds"], 0)
            self.assertIn("simulated_work", report["stage_timings"])
            self.assertGreater(len(report["optimizations_applied"]), 0)
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
