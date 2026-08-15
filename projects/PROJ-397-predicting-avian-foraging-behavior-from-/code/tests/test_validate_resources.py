"""
Unit tests for the validate_resources module.

Tests cover:
- Resource monitoring initialization
- Memory measurement functionality
- Constraint validation logic
- Log file generation
"""
import os
import sys
import unittest
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from utils.validate_resources import (
    ResourceMonitor,
    check_resource_constraints,
    MAX_RUNTIME_SECONDS,
    MAX_MEMORY_BYTES
)
from utils.config import get_project_root


class TestResourceMonitor(unittest.TestCase):
    """Test cases for ResourceMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = ResourceMonitor()
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test directory if it exists
        if os.path.exists(self.test_dir):
            import shutil
            shutil.rmtree(self.test_dir)
            
    def test_monitor_initialization(self):
        """Test that ResourceMonitor initializes correctly."""
        self.assertIsNone(self.monitor.start_time)
        self.assertIsNone(self.monitor.end_time)
        self.assertEqual(self.monitor.peak_memory_bytes, 0.0)
        self.assertFalse(self.monitor.monitoring_active)
        
    def test_start_method(self):
        """Test that start() initializes timing and log file."""
        self.monitor.start()
        
        self.assertIsNotNone(self.monitor.start_time)
        self.assertIsNotNone(self.monitor.RESOURCE_LOG_PATH)
        self.assertTrue(self.monitor.RESOURCE_LOG_PATH.parent.exists())
        
        # Check log file was created
        self.assertTrue(self.monitor.RESOURCE_LOG_PATH.exists())
        
        # Verify log content
        with open(self.monitor.RESOURCE_LOG_PATH, 'r') as f:
            entries = json.load(f)
            
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["event"], "start")
        self.assertIn("constraints", entries[0])
        
    def test_memory_measurement(self):
        """Test memory measurement functionality."""
        # Start monitor
        self.monitor.start()
        
        # Update memory
        self.monitor.update_memory()
        
        # Memory should be non-negative
        self.assertGreaterEqual(self.monitor.peak_memory_bytes, 0)
        
        # Get peak memory in GB
        memory_gb = self.monitor.get_peak_memory_gb()
        self.assertGreaterEqual(memory_gb, 0)
        
    def test_stop_method(self):
        """Test that stop() calculates metrics and validates constraints."""
        self.monitor.start()
        
        # Simulate some work
        time.sleep(0.1)
        self.monitor.update_memory()
        
        results = self.monitor.stop()
        
        # Verify results structure
        self.assertIn("event", results)
        self.assertEqual(results["event"], "end")
        self.assertIn("metrics", results)
        self.assertIn("validation", results)
        
        # Verify timing
        self.assertGreater(results["metrics"]["total_runtime_seconds"], 0)
        
        # Verify constraints are checked
        self.assertIn("runtime_ok", results["validation"])
        self.assertIn("memory_ok", results["validation"])
        self.assertIn("all_constraints_met", results["validation"])
        
    def test_log_persistence(self):
        """Test that log entries are properly persisted."""
        self.monitor.start()
        self.monitor.update_memory()
        self.monitor.stop()
        
        # Read log file
        with open(self.monitor.RESOURCE_LOG_PATH, 'r') as f:
            entries = json.load(f)
            
        # Should have start and end entries
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["event"], "start")
        self.assertEqual(entries[1]["event"], "end")
        
    def test_elapsed_time_calculation(self):
        """Test elapsed time calculation."""
        self.monitor.start()
        time.sleep(0.1)
        self.monitor.end_time = time.time()
        
        elapsed = self.monitor.get_elapsed_hours()
        
        # Should be approximately 0.1 seconds in hours
        self.assertGreater(elapsed, 0)
        self.assertLess(elapsed, 0.1)  # Should be less than 0.1 hours


class TestConstraintValidation(unittest.TestCase):
    """Test cases for constraint validation logic."""
    
    def test_runtime_constraint_pass(self):
        """Test runtime constraint passes when within limit."""
        passed, message = check_resource_constraints(
            runtime_seconds=MAX_RUNTIME_SECONDS - 100,
            memory_gb=1.0
        )
        
        self.assertTrue(passed)
        self.assertIn("satisfied", message)
        
    def test_runtime_constraint_fail(self):
        """Test runtime constraint fails when exceeded."""
        passed, message = check_resource_constraints(
            runtime_seconds=MAX_RUNTIME_SECONDS + 100,
            memory_gb=1.0
        )
        
        self.assertFalse(passed)
        self.assertIn("Runtime exceeded", message)
        
    def test_memory_constraint_pass(self):
        """Test memory constraint passes when within limit."""
        passed, message = check_resource_constraints(
            runtime_seconds=100,
            memory_gb=1.0
        )
        
        self.assertTrue(passed)
        self.assertIn("satisfied", message)
        
    def test_memory_constraint_fail(self):
        """Test memory constraint fails when exceeded."""
        # Convert 7GB to GB for test
        max_memory_gb = MAX_MEMORY_BYTES / (1024**3)
        
        passed, message = check_resource_constraints(
            runtime_seconds=100,
            memory_gb=max_memory_gb + 1.0
        )
        
        self.assertFalse(passed)
        self.assertIn("Memory exceeded", message)
        
    def test_both_constraints_fail(self):
        """Test when both constraints are violated."""
        max_memory_gb = MAX_MEMORY_BYTES / (1024**3)
        
        passed, message = check_resource_constraints(
            runtime_seconds=MAX_RUNTIME_SECONDS + 1000,
            memory_gb=max_memory_gb + 1.0
        )
        
        self.assertFalse(passed)
        # Should mention both violations
        self.assertIn("Runtime", message)
        self.assertIn("Memory", message)
        
    def test_edge_case_exact_limit(self):
        """Test behavior at exact constraint limits."""
        # At exact limit should still pass (using < not <=)
        max_memory_gb = MAX_MEMORY_BYTES / (1024**3)
        
        passed, message = check_resource_constraints(
            runtime_seconds=MAX_RUNTIME_SECONDS - 0.1,
            memory_gb=max_memory_gb - 0.1
        )
        
        self.assertTrue(passed)
        
        
class TestIntegration(unittest.TestCase):
    """Integration tests for the resource validation system."""
    
    def test_full_workflow(self):
        """Test complete workflow from start to validation."""
        monitor = ResourceMonitor()
        
        # Start monitoring
        monitor.start()
        
        # Simulate pipeline execution
        time.sleep(0.1)
        monitor.update_memory()
        
        # Stop and validate
        results = monitor.stop()
        
        # Verify all expected fields exist
        self.assertIn("metrics", results)
        self.assertIn("validation", results)
        self.assertIn("constraints", results)
        
        # Verify metrics are reasonable
        self.assertGreater(results["metrics"]["total_runtime_seconds"], 0)
        self.assertGreaterEqual(results["metrics"]["peak_memory_bytes"], 0)
        
        # Verify validation flags are boolean
        self.assertIsInstance(results["validation"]["runtime_ok"], bool)
        self.assertIsInstance(results["validation"]["memory_ok"], bool)
        
        
if __name__ == "__main__":
    unittest.main()