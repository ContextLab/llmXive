"""
Unit tests for profiler module (T041).
"""
import os
import json
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.profiler import (
    profile_function,
    profile_pipeline,
    generate_profile_report,
    PROFILE_OUTPUT_DIR
)

class TestProfiler(unittest.TestCase):
    """Test cases for profiling functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_profile_dir = Path(tempfile.mkdtemp())
        self.original_profile_dir = PROFILE_OUTPUT_DIR
        
        # Mock profile output directory
        import code.profiler
        code.profiler.PROFILE_OUTPUT_DIR = self.test_profile_dir

    def tearDown(self):
        """Clean up test fixtures."""
        if self.test_profile_dir.exists():
            shutil.rmtree(self.test_profile_dir)

    def test_profile_function_basic(self):
        """Test basic function profiling."""
        def test_func(x):
            return x * 2
        
        result = profile_function(test_func, 5, output_file=None)
        
        self.assertEqual(result, 10)

    def test_profile_function_with_output(self):
        """Test function profiling with output file."""
        def test_func(x):
            time.sleep(0.05)
            return x + 1
        
        result = profile_function(
            test_func, 
            10, 
            output_file=Path("test_profile.json")
        )
        
        self.assertEqual(result, 11)
        
        # Check that profile file was created
        profile_path = self.test_profile_dir / "test_profile.json"
        self.assertTrue(profile_path.exists())
        
        with open(profile_path, 'r') as f:
            profile_data = json.load(f)
        
        self.assertIn("execution_time_seconds", profile_data)
        self.assertGreater(profile_data["execution_time_seconds"], 0)

    def test_profile_function_error_handling(self):
        """Test profiling with function that raises an error."""
        def failing_func(x):
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError):
            profile_function(failing_func, 5)

    def test_generate_profile_report(self):
        """Test generating combined profile report."""
        # Create mock profile files
        profile1 = self.test_profile_dir / "profile1.json"
        profile2 = self.test_profile_dir / "profile2.json"
        
        with open(profile1, 'w') as f:
            json.dump({"function": "test1", "time": 0.1}, f)
        
        with open(profile2, 'w') as f:
            json.dump({"function": "test2", "time": 0.2}, f)
        
        report_path = generate_profile_report([profile1, profile2])
        
        self.assertTrue(report_path.exists())
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        self.assertEqual(len(report["profiles"]), 2)

    def test_profile_pipeline(self):
        """Test pipeline profiling."""
        def mock_pipeline(organism, threshold):
            time.sleep(0.05)
            return {"organism": organism, "threshold": threshold, "status": "success"}
        
        result = profile_pipeline(
            mock_pipeline,
            "human",
            700,
            output_file="pipeline_test.json"
        )
        
        self.assertEqual(result["organism"], "human")
        self.assertEqual(result["threshold"], 700)
        self.assertEqual(result["status"], "success")

if __name__ == "__main__":
    unittest.main()