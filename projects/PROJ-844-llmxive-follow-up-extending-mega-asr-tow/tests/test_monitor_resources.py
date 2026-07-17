"""
Unit tests for code/monitor_resources.py
"""

import os
import sys
import json
import tempfile
import time
import unittest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from monitor_resources import ResourceMonitor, monitor_resources


class TestResourceMonitor(unittest.TestCase):

    def test_init(self):
        """Test initialization of ResourceMonitor."""
        monitor = ResourceMonitor()
        self.assertEqual(monitor.start_time, 0.0)
        self.assertEqual(monitor.peak_rss, 0)
        self.assertEqual(monitor.elapsed_time, 0.0)
        self.assertFalse(monitor._running)

    @unittest.skipIf(sys.platform == "win32", "Resource module not available on Windows")
    def test_start_stop(self):
        """Test start and stop functionality."""
        monitor = ResourceMonitor()
        monitor.start()
        self.assertTrue(monitor._running)
        self.assertGreater(monitor.start_time, 0)

        time.sleep(0.1)
        monitor.stop()

        self.assertFalse(monitor._running)
        self.assertGreater(monitor.elapsed_time, 0)

    @unittest.skipIf(sys.platform == "win32", "Resource module not available on Windows")
    def test_context_manager(self):
        """Test the context manager usage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_report.json")
            
            with monitor_resources(output_file=output_path) as monitor:
                # Do some dummy work
                _ = [i * i for i in range(1000)]
                time.sleep(0.05)
            
            # Check file exists
            self.assertTrue(os.path.exists(output_path))
            
            # Check content
            with open(output_path, "r") as f:
                report = json.load(f)
            
            self.assertIn("peak_rss_bytes", report)
            self.assertIn("peak_rss_mb", report)
            self.assertIn("elapsed_time_seconds", report)
            self.assertGreater(report["elapsed_time_seconds"], 0)
            self.assertGreater(report["peak_rss_bytes"], 0)

    @unittest.skipIf(sys.platform == "win32", "Resource module not available on Windows")
    def test_report_values(self):
        """Test that report values are reasonable."""
        monitor = ResourceMonitor()
        monitor.start()
        
        # Do some work
        data = []
        for i in range(100000):
            data.append(i)
        
        monitor.stop()
        
        report = monitor.get_report()
        
        self.assertIsInstance(report["peak_rss_bytes"], int)
        self.assertIsInstance(report["peak_rss_mb"], float)
        self.assertIsInstance(report["elapsed_time_seconds"], float)
        
        # RSS should be positive
        self.assertGreater(report["peak_rss_bytes"], 0)
        # Time should be positive
        self.assertGreater(report["elapsed_time_seconds"], 0)
        # MB conversion should be consistent
        self.assertAlmostEqual(
            report["peak_rss_mb"], 
            report["peak_rss_bytes"] / (1024 * 1024), 
            places=5
        )

    def test_stop_without_start(self):
        """Test that stopping without starting is safe."""
        monitor = ResourceMonitor()
        # Should not raise an error
        monitor.stop()
        self.assertEqual(monitor.elapsed_time, 0.0)

    def test_update_without_start(self):
        """Test that updating without starting is safe."""
        monitor = ResourceMonitor()
        # Should not raise an error
        monitor.update()
        self.assertEqual(monitor.peak_rss, 0)


if __name__ == "__main__":
    unittest.main()