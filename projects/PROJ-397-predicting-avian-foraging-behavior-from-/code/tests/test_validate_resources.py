"""
Tests for the validate_resources module.

These tests verify:
- ResourceMonitor class functionality
- Constraint validation logic
- Integration with pipeline execution
"""

import os
import sys
import unittest
import tempfile
import json
import time
from pathlib import Path
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.validate_resources import (
    ResourceMonitor,
    validate_pipeline_resources,
    check_resource_constraints,
    MAX_RUNTIME_SECONDS,
    MAX_MEMORY_BYTES
)
from utils.config import get_project_root


class TestResourceMonitor(unittest.TestCase):
    """Test cases for the ResourceMonitor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test that ResourceMonitor initializes correctly."""
        monitor = ResourceMonitor(self.project_root)
        self.assertEqual(monitor.project_root, self.project_root)
        self.assertIsNone(monitor.start_time)
        self.assertIsNone(monitor.end_time)
        self.assertEqual(monitor.peak_memory_bytes, 0)
        self.assertEqual(monitor.log_file, self.project_root / "data" / "resource_monitor.json")

    def test_start_and_stop(self):
        """Test start and stop methods."""
        monitor = ResourceMonitor(self.project_root)

        # Before start
        self.assertIsNone(monitor.start_time)

        # Start monitoring
        monitor.start()
        self.assertIsNotNone(monitor.start_time)
        start_time = monitor.start_time

        # Small delay
        time.sleep(0.1)

        # Stop monitoring
        monitor.stop()
        self.assertIsNotNone(monitor.end_time)
        self.assertGreater(monitor.end_time, start_time)

        # Verify runtime calculation
        runtime = monitor.get_runtime_seconds()
        self.assertGreater(runtime, 0.0)
        self.assertLess(runtime, 1.0)  # Should be less than 1 second

    def test_get_runtime_seconds(self):
        """Test runtime calculation."""
        monitor = ResourceMonitor(self.project_root)

        # Without start/stop
        self.assertEqual(monitor.get_runtime_seconds(), 0.0)

        # With start/stop
        monitor.start()
        time.sleep(0.1)
        monitor.stop()

        runtime = monitor.get_runtime_seconds()
        self.assertGreater(runtime, 0.0)
        self.assertLess(runtime, 1.0)

    def test_get_peak_memory_gb(self):
        """Test peak memory calculation."""
        monitor = ResourceMonitor(self.project_root)

        # Before any memory measurement
        self.assertEqual(monitor.get_peak_memory_gb(), 0.0)

        # After stop (which measures memory)
        monitor.start()
        # Do some memory allocation
        data = [i for i in range(100000)]
        monitor.stop()

        peak_memory_gb = monitor.get_peak_memory_gb()
        self.assertGreater(peak_memory_gb, 0.0)
        # Should be reasonable (less than 1 GB for this test)
        self.assertLess(peak_memory_gb, 1.0)

    def test_validate_constraints_pass(self):
        """Test constraint validation when within limits."""
        monitor = ResourceMonitor(self.project_root)
        monitor.start()
        # Simulate a short runtime
        time.sleep(0.1)
        monitor.stop()

        # Manually set a low memory usage for testing
        monitor.peak_memory_bytes = 100 * 1024 * 1024  # 100 MB

        is_valid, details = monitor.validate_constraints()

        self.assertTrue(is_valid)
        self.assertTrue(details['runtime_valid'])
        self.assertTrue(details['memory_valid'])
        self.assertGreater(details['runtime_seconds'], 0)
        self.assertGreater(details['peak_memory_gb'], 0)

    def test_validate_constraints_fail_runtime(self):
        """Test constraint validation when runtime exceeds limit."""
        monitor = ResourceMonitor(self.project_root)

        # Simulate excessive runtime
        monitor.start_time = time.time() - (MAX_RUNTIME_SECONDS + 100)
        monitor.end_time = time.time()
        monitor.peak_memory_bytes = 100 * 1024 * 1024  # 100 MB

        is_valid, details = monitor.validate_constraints()

        self.assertFalse(is_valid)
        self.assertFalse(details['runtime_valid'])
        self.assertTrue(details['memory_valid'])

    def test_validate_constraints_fail_memory(self):
        """Test constraint validation when memory exceeds limit."""
        monitor = ResourceMonitor(self.project_root)
        monitor.start()
        monitor.stop()

        # Simulate excessive memory usage
        monitor.peak_memory_bytes = MAX_MEMORY_BYTES + 1024 * 1024 * 1024  # 8 GB

        is_valid, details = monitor.validate_constraints()

        self.assertFalse(is_valid)
        self.assertTrue(details['runtime_valid'])
        self.assertFalse(details['memory_valid'])

    def test_save_report(self):
        """Test that report is saved correctly."""
        monitor = ResourceMonitor(self.project_root)
        monitor.start()
        time.sleep(0.05)
        monitor.stop()

        is_valid, details = monitor.validate_constraints()
        monitor.save_report(details)

        # Verify file exists
        self.assertTrue(monitor.log_file.exists())

        # Verify content
        with open(monitor.log_file, 'r') as f:
            report = json.load(f)

        self.assertIn('timestamp', report)
        self.assertIn('project_root', report)
        self.assertIn('constraints', report)
        self.assertIn('results', report)
        self.assertEqual(report['results'], details)

    def test_log_summary(self):
        """Test that summary is logged correctly."""
        # This test just verifies the method doesn't crash
        monitor = ResourceMonitor(self.project_root)
        monitor.start()
        monitor.stop()

        is_valid, details = monitor.validate_constraints()
        # Should not raise any exceptions
        monitor.log_summary(details)


class TestConstraintValidation(unittest.TestCase):
    """Test cases for constraint validation functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_pipeline_resources(self):
        """Test the validate_pipeline_resources function."""
        is_valid, details = validate_pipeline_resources(self.project_root)

        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(details, dict)
        self.assertIn('runtime_seconds', details)
        self.assertIn('peak_memory_gb', details)
        self.assertIn('runtime_valid', details)
        self.assertIn('memory_valid', details)
        self.assertIn('all_valid', details)

    def test_check_resource_constraints(self):
        """Test the check_resource_constraints function."""
        # This should return True since we're not actually running a heavy pipeline
        result = check_resource_constraints(self.project_root)
        self.assertIsInstance(result, bool)


class TestIntegration(unittest.TestCase):
    """Integration tests for the validate_resources module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create necessary directories
        (self.project_root / "data").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_workflow(self):
        """Test the full resource monitoring workflow."""
        monitor = ResourceMonitor(self.project_root)

        # Start monitoring
        monitor.start()

        # Simulate some work
        time.sleep(0.1)
        data = [i ** 2 for i in range(10000)]

        # Stop monitoring
        monitor.stop()

        # Validate constraints
        is_valid, details = monitor.validate_constraints()

        # Save report
        monitor.save_report(details)

        # Log summary
        monitor.log_summary(details)

        # Verify all steps completed
        self.assertTrue(monitor.log_file.exists())
        self.assertGreater(monitor.get_runtime_seconds(), 0)
        self.assertGreater(monitor.get_peak_memory_gb(), 0)

    def test_report_structure(self):
        """Test that the report has the correct structure."""
        monitor = ResourceMonitor(self.project_root)
        monitor.start()
        time.sleep(0.05)
        monitor.stop()

        is_valid, details = monitor.validate_constraints()
        monitor.save_report(details)

        with open(monitor.log_file, 'r') as f:
            report = json.load(f)

        # Verify top-level structure
        self.assertIn('timestamp', report)
        self.assertIn('project_root', report)
        self.assertIn('constraints', report)
        self.assertIn('results', report)

        # Verify constraints structure
        self.assertIn('max_runtime_seconds', report['constraints'])
        self.assertIn('max_memory_gb', report['constraints'])
        self.assertEqual(report['constraints']['max_runtime_seconds'], MAX_RUNTIME_SECONDS)
        self.assertEqual(report['constraints']['max_memory_gb'], MAX_MEMORY_BYTES / (1024**3))

        # Verify results structure
        results = report['results']
        self.assertIn('runtime_seconds', results)
        self.assertIn('peak_memory_gb', results)
        self.assertIn('runtime_valid', results)
        self.assertIn('memory_valid', results)
        self.assertIn('all_valid', results)
        self.assertIn('max_runtime_seconds', results)
        self.assertIn('max_memory_gb', results)


if __name__ == '__main__':
    unittest.main()