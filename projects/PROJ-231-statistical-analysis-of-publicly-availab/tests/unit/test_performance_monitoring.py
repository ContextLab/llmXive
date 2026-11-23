"""
Unit tests for performance monitoring and compliance reporting (T035).
"""
import unittest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from monitoring_utils import get_memory_usage_mb, get_disk_usage_gb, check_compliance
from config import get_artifacts_dir

class TestPerformanceMonitoring(unittest.TestCase):

    def test_get_memory_usage_mb_returns_positive(self):
        """Test that get_memory_usage_mb returns a non-negative value."""
        memory = get_memory_usage_mb()
        self.assertGreaterEqual(memory, 0)
        self.assertIsInstance(memory, float)

    def test_get_disk_usage_gb_returns_positive(self):
        """Test that get_disk_usage_gb returns a non-negative value."""
        disk = get_disk_usage_gb()
        self.assertGreaterEqual(disk, 0)
        self.assertIsInstance(disk, float)

    def test_check_compliance_pass(self):
        """Test compliance check when all metrics are within limits."""
        limits = {
            "max_runtime_seconds": 100,
            "max_memory_mb": 1000,
            "max_disk_gb": 10
        }
        thresholds = {
            "runtime_seconds": 80,
            "memory_mb": 800,
            "disk_gb": 8
        }

        result = check_compliance(50, 500, 5, limits, thresholds)

        self.assertEqual(result["compliance_status"]["runtime"], "PASS")
        self.assertEqual(result["compliance_status"]["memory"], "PASS")
        self.assertEqual(result["compliance_status"]["disk"], "PASS")
        self.assertEqual(result["overall_status"], "COMPLIANT")
        self.assertEqual(len(result["warnings"]), 0)

    def test_check_compliance_fail_runtime(self):
        """Test compliance check when runtime exceeds limit."""
        limits = {
            "max_runtime_seconds": 100,
            "max_memory_mb": 1000,
            "max_disk_gb": 10
        }
        thresholds = {
            "runtime_seconds": 80,
            "memory_mb": 800,
            "disk_gb": 8
        }

        result = check_compliance(110, 500, 5, limits, thresholds)

        self.assertEqual(result["compliance_status"]["runtime"], "FAIL")
        self.assertEqual(result["overall_status"], "NON-COMPLIANT")
        self.assertIn("Runtime", result["warnings"][0])

    def test_check_compliance_warning_memory(self):
        """Test compliance check when memory exceeds threshold but not limit."""
        limits = {
            "max_runtime_seconds": 100,
            "max_memory_mb": 1000,
            "max_disk_gb": 10
        }
        thresholds = {
            "runtime_seconds": 80,
            "memory_mb": 800,
            "disk_gb": 8
        }

        result = check_compliance(50, 900, 5, limits, thresholds)

        self.assertEqual(result["compliance_status"]["memory"], "PASS")
        self.assertEqual(result["overall_status"], "COMPLIANT")
        self.assertIn("Peak memory", result["warnings"][0])

if __name__ == "__main__":
    unittest.main()
