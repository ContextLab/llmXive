"""
Unit tests for External Validation Protocol (T066).

Verifies that the validator rejects any attempt by the model to modify
the benchmark set, ensuring the "External Validation" invariant holds.
"""

import unittest
import os
import sys
import tempfile
import json
from unittest.mock import patch, MagicMock

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from pipeline.external_validator import (
    ExternalValidator, 
    BenchmarkTamperError, 
    get_immutable_benchmarks,
    IMMUTABLE_BENCHMARKS
)
from config import get_config, set_config

class TestExternalValidator(unittest.TestCase):
    
    def setUp(self):
        """Set up a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.results_dir = os.path.join(self.temp_dir, "results")
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Mock the config to point to our temp directory
        mock_config = MagicMock()
        mock_config.path_config.results_dir = self.results_dir
        
        # Patch get_config to return our mock
        self.config_patcher = patch('pipeline.external_validator.get_config', return_value=mock_config)
        self.mock_get_config = self.config_patcher.start()

    def tearDown(self):
        """Clean up temporary files."""
        self.config_patcher.stop()
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_valid_benchmark_selection(self):
        """Test that the correct set of benchmarks passes validation."""
        validator = ExternalValidator()
        valid_benchmarks = ["gsm8k", "arc_challenge", "wikitext2"]
        
        # Should not raise
        result = validator.validate_benchmark_selection(valid_benchmarks)
        self.assertTrue(result)

    def test_missing_benchmark_raises_error(self):
        """Test that removing a benchmark raises BenchmarkTamperError."""
        validator = ExternalValidator()
        incomplete_benchmarks = ["gsm8k", "arc_challenge"] # Missing wikitext2
        
        with self.assertRaises(BenchmarkTamperError) as context:
            validator.validate_benchmark_selection(incomplete_benchmarks)
        
        self.assertIn("Missing", str(context.exception))
        self.assertIn("wikitext2", str(context.exception))

    def test_extra_benchmark_raises_error(self):
        """Test that adding an unauthorized benchmark raises BenchmarkTamperError."""
        validator = ExternalValidator()
        extra_benchmarks = ["gsm8k", "arc_challenge", "wikitext2", "custom_math"]
        
        with self.assertRaises(BenchmarkTamperError) as context:
            validator.validate_benchmark_selection(extra_benchmarks)
        
        self.assertIn("Extra", str(context.exception))
        self.assertIn("custom_math", str(context.exception))

    def test_case_insensitivity(self):
        """Test that benchmark names are case-insensitive."""
        validator = ExternalValidator()
        mixed_case = ["GSM8K", "Arc_Challenge", "WIKITEXT2"]
        
        # Should pass
        result = validator.validate_benchmark_selection(mixed_case)
        self.assertTrue(result)

    def test_forbidden_config_keys(self):
        """Test that forbidden keys in config raise BenchmarkTamperError."""
        validator = ExternalValidator()
        
        # Config with a key that implies dynamic selection
        malicious_config = {
            "benchmarks": ["gsm8k", "arc_challenge", "wikitext2"],
            "dynamic_selection": True
        }
        
        with self.assertRaises(BenchmarkTamperError) as context:
            validator.validate_evaluation_config(malicious_config)
        
        self.assertIn("unauthorized configuration keys", str(context.exception))
        self.assertIn("dynamic_selection", str(context.exception))

    def test_enforce_method_integration(self):
        """Test the main enforcement method with a valid request."""
        validator = ExternalValidator()
        request = {
            "cycle_number": 1,
            "config": {
                "benchmarks": ["gsm8k", "arc_challenge", "wikitext2"]
            }
        }
        
        # Should return the request unchanged
        result = validator.enforce(request)
        self.assertEqual(result, request)

    def test_enforce_method_rejection(self):
        """Test the main enforcement method rejects a tampered request."""
        validator = ExternalValidator()
        request = {
            "cycle_number": 2,
            "config": {
                "benchmarks": ["gsm8k"] # Missing others
            }
        }
        
        with self.assertRaises(BenchmarkTamperError):
            validator.enforce(request)

    def test_log_file_creation(self):
        """Verify that validation attempts are logged."""
        validator = ExternalValidator()
        validator.validate_benchmark_selection(["gsm8k", "arc_challenge", "wikitext2"])
        
        log_path = os.path.join(self.results_dir, "validation.log")
        self.assertTrue(os.path.exists(log_path))
        
        with open(log_path, 'r') as f:
            content = f.read()
            self.assertIn("Validation passed", content)

    def test_immutable_benchmarks_function(self):
        """Test the helper function returns the correct list."""
        benchmarks = get_immutable_benchmarks()
        self.assertEqual(benchmarks, sorted(list(IMMUTABLE_BENCHMARKS)))
        self.assertIsInstance(benchmarks, list)

if __name__ == '__main__':
    unittest.main()