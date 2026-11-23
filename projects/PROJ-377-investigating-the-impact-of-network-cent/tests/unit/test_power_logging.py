"""
Unit Tests for Power Logging (T004b)

Tests the logic for logging power warnings and updating the reproducibility report.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.power_logging import (
    log_power_warning, 
    update_reproducibility_report, 
    load_power_check_results,
    REPRODUCIBILITY_REPORT_PATH,
    POWER_METRICS_PATH
)

class TestPowerLogging(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary directories and mock files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.power_metrics_path = Path(self.temp_dir) / "power_metrics.json"
        self.report_path = Path(self.temp_dir) / "reproducibility_report.json"
        
        # Mock the global paths in the module
        self.original_power_path = POWER_METRICS_PATH
        self.original_report_path = REPRODUCIBILITY_REPORT_PATH
        
        # We will patch the functions that use these paths directly in the test methods
        # or pass custom paths to helper functions if we refactor. 
        # For now, we test the logic functions that don't rely on global paths directly.

    def tearDown(self):
        """Clean up temporary directories."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_power_warning_underpowered(self):
        """Test warning when N < 50."""
        data = {"n_subjects": 40, "threshold": 50}
        message, warning_flag = log_power_warning(data)
        
        self.assertTrue(warning_flag)
        self.assertIn("Underpowered", message)
        self.assertIn("40", message)

    def test_log_power_warning_limited(self):
        """Test warning when 50 <= N < 85."""
        data = {"n_subjects": 60, "threshold": 50}
        message, warning_flag = log_power_warning(data)
        
        self.assertFalse(warning_flag)
        self.assertIn("N < 85", message)
        self.assertIn("60", message)

    def test_log_power_warning_success(self):
        """Test success when N >= 85."""
        data = {"n_subjects": 100, "threshold": 50}
        message, warning_flag = log_power_warning(data)
        
        self.assertFalse(warning_flag)
        self.assertIn("Power check passed", message)
        self.assertIn("100", message)

    def test_update_reproducibility_report(self):
        """Test that the report is updated correctly."""
        # Create a temporary report file
        with open(self.report_path, 'w') as f:
            json.dump({"pipeline_metrics": {}}, f)
        
        # Patch the load and save functions to use our temp file
        with patch('code.data.power_logging.load_reproducibility_report') as mock_load, \
             patch('code.data.power_logging.save_reproducibility_report') as mock_save:
             
            mock_load.return_value = {"pipeline_metrics": {}}
            
            update_reproducibility_report(True, "Test message")
            
            # Verify save was called with correct structure
            mock_save.assert_called_once()
            call_args = mock_save.call_args[0][0]
            
            self.assertTrue(call_args["pipeline_metrics"]["power_warning"])
            self.assertEqual(call_args["pipeline_metrics"]["power_check_message"], "Test message")

if __name__ == '__main__':
    unittest.main()