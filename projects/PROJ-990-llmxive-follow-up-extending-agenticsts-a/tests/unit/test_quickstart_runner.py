"""
Unit tests for the Quickstart Validation Runner.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is in path
import sys
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

class TestQuickstartRunner(unittest.TestCase):

    def test_check_file_exists_positive(self):
        """Test check_file_exists with an existing file."""
        from quickstart_runner import check_file_exists
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = Path(f.name)
        
        try:
            result = check_file_exists(temp_path, "test file")
            self.assertTrue(result)
        finally:
            os.unlink(temp_path)

    def test_check_file_exists_missing(self):
        """Test check_file_exists with a missing file."""
        from quickstart_runner import check_file_exists
        temp_path = Path("/tmp/does_not_exist_12345.txt")
        result = check_file_exists(temp_path, "missing file")
        self.assertFalse(result)

    def test_load_json_safe_valid(self):
        """Test load_json_safe with valid JSON."""
        from quickstart_runner import load_json_safe
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({"key": "value"}, f)
            temp_path = Path(f.name)
        
        try:
            result = load_json_safe(temp_path)
            self.assertEqual(result, {"key": "value"})
        finally:
            os.unlink(temp_path)

    def test_load_json_safe_invalid(self):
        """Test load_json_safe with invalid JSON."""
        from quickstart_runner import load_json_safe
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write("not valid json")
            temp_path = Path(f.name)
        
        try:
            result = load_json_safe(temp_path)
            self.assertEqual(result, {})
        finally:
            os.unlink(temp_path)

    @patch('quickstart_runner.load_config_from_file')
    @patch('quickstart_runner.ensure_directories')
    @patch('quickstart_runner.validate_config')
    def test_run_quickstart_validation_setup(self, mock_validate, mock_ensure, mock_load):
        """Test that setup stage runs correctly."""
        from quickstart_runner import run_quickstart_validation
        
        mock_load.return_value = {"token_budget": 4096}
        
        # Mock all subsequent stages to avoid actual execution
        with patch('quickstart_runner.validate_data_source', return_value=True), \
             patch('quickstart_runner.parse_trajectories'), \
             patch('quickstart_runner.stratified_split'), \
             patch('quickstart_runner.process_trajectories'), \
             patch('quickstart_runner.run_ablation_study'), \
             patch('quickstart_runner.run_training'), \
             patch('quickstart_runner.run_dynamic_simulation'), \
             patch('quickstart_runner.run_baseline_simulation'), \
             patch('quickstart_runner.generate_baseline_comparison'), \
             patch('quickstart_runner.calculate_reduction'), \
             patch('quickstart_runner.detect_divergence'), \
             patch('quickstart_runner.save_statistical_results'), \
             patch('quickstart_runner.generate_final_report'), \
             patch('quickstart_runner.check_file_exists', return_value=True):
            
            result = run_quickstart_validation()
            self.assertTrue(result)
            mock_load.assert_called_once()
            mock_ensure.assert_called_once()
            mock_validate.assert_called_once()

if __name__ == '__main__':
    unittest.main()