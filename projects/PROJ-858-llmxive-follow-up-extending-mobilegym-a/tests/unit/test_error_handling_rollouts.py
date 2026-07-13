"""
Unit tests for error handling in rollout processing (T027).
Verifies that malformed JSON rollouts are skipped without crashing the batch.
"""
import json
import os
import tempfile
import unittest

from scheduler.error_handling_rollouts import (
    load_rollout_safe,
    process_rollout_batch
)

class TestRolloutErrorHandling(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp(prefix="test_rollout_")
        
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_load_valid_json(self):
        """Test loading a valid JSON file."""
        data = {"key": "value"}
        path = os.path.join(self.temp_dir, "valid.json")
        with open(path, 'w') as f:
            json.dump(data, f)
            
        result, status = load_rollout_safe(path)
        
        self.assertEqual(status, "success")
        self.assertEqual(result, data)
        
    def test_load_invalid_json_syntax(self):
        """Test loading a file with invalid JSON syntax."""
        path = os.path.join(self.temp_dir, "invalid.json")
        with open(path, 'w') as f:
            f.write("{ this is not valid json }")
            
        result, status = load_rollout_safe(path)
        
        self.assertIsNone(result)
        self.assertTrue(status.startswith("error: Invalid JSON syntax"))
        
    def test_load_non_dict_json(self):
        """Test loading a JSON file that is not a dictionary."""
        data = [1, 2, 3]
        path = os.path.join(self.temp_dir, "list.json")
        with open(path, 'w') as f:
            json.dump(data, f)
            
        result, status = load_rollout_safe(path)
        
        self.assertIsNone(result)
        self.assertTrue(status.startswith("error: Malformed JSON structure"))
        
    def test_load_missing_file(self):
        """Test loading a non-existent file."""
        path = os.path.join(self.temp_dir, "nonexistent.json")
        
        result, status = load_rollout_safe(path)
        
        self.assertIsNone(result)
        self.assertTrue(status.startswith("error: File not found"))
        
    def test_process_batch_skips_malformed(self):
        """Test that process_rollout_batch skips malformed files without crashing."""
        # Create files
        valid_data = {"task": "valid"}
        valid_path = os.path.join(self.temp_dir, "valid.json")
        with open(valid_path, 'w') as f:
            json.dump(valid_data, f)
            
        invalid_path = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_path, 'w') as f:
            f.write("{ bad }")
            
        missing_path = os.path.join(self.temp_dir, "missing.json")
        
        batch = [valid_path, invalid_path, missing_path]
        
        def processor(data):
            return data["task"]
            
        # Should not raise an exception
        results = process_rollout_batch(batch, processor)
        
        # Check results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["path"], valid_path)
        self.assertEqual(results[0]["status"], "success")
        self.assertEqual(results[0]["result"], "valid")

if __name__ == "__main__":
    unittest.main()
