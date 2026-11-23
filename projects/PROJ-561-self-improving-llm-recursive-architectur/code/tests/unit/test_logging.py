import unittest
import os
import sys
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.logging import init_cycle_logger, log_cycle_event, log_authority_trace, get_log_path
from config import get_config

class MockConfig:
    """Mock config for testing log paths."""
    def __init__(self):
        self.log_path = "/tmp/test_logs/cycle_1.log"

class TestLogging(unittest.TestCase):
    def setUp(self):
        """Set up a temporary directory for logs."""
        self.test_dir = tempfile.mkdtemp()
        self.original_config = get_config()
        
        # Mock the config to use our temp directory
        mock_cfg = MockConfig()
        mock_cfg.log_path = os.path.join(self.test_dir, "cycle_1.log")
        
        # Patch get_config to return our mock
        self.config_patcher = patch('utils.logging.get_config', return_value=mock_cfg)
        self.config_patcher.start()
        self.config_patcher2 = patch('config.get_config', return_value=mock_cfg)
        self.config_patcher2.start()

    def tearDown(self):
        """Clean up temporary directory."""
        self.config_patcher.stop()
        self.config_patcher2.stop()
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_cycle_logger_creates_file(self):
        """Test that init_cycle_logger creates the log file."""
        logger = init_cycle_logger(1)
        log_path = get_log_path(1)
        self.assertTrue(os.path.exists(log_path), f"Log file {log_path} should exist")
        self.assertIsInstance(logger, logging.Logger)

    def test_log_cycle_event_writes_json(self):
        """Test that log_cycle_event writes a valid JSON line."""
        logger = init_cycle_logger(1)
        log_path = get_log_path(1)
        
        event_data = {"test_key": "test_value", "number": 42}
        log_cycle_event(logger, "test_event", event_data)
        
        # Read the file and verify JSON
        with open(log_path, 'r') as f:
            line = f.readline().strip()
            parsed = json.loads(line)
            
            self.assertEqual(parsed['event_type'], 'test_event')
            self.assertEqual(parsed['data']['test_key'], 'test_value')
            self.assertIn('timestamp', parsed)

    def test_log_authority_trace_structure(self):
        """Test that log_authority_trace writes the correct Authority Trace structure."""
        logger = init_cycle_logger(1)
        log_path = get_log_path(1)
        
        proposal_id = "prop_123"
        benchmark_score = {"gsm8k": 0.85, "arc": 0.90}
        oracle_result = {"passed": True, "reason": "Within limits"}
        human_constraints = {"max_param_increase_ratio": 0.30}
        
        log_authority_trace(
            logger, 
            proposal_id, 
            benchmark_score, 
            oracle_result, 
            human_constraints
        )
        
        with open(log_path, 'r') as f:
            line = f.readline().strip()
            parsed = json.loads(line)
            
            # Verify structure
            self.assertIn('authority_trace', parsed)
            trace = parsed['authority_trace']
            
            self.assertEqual(trace['proposal_id'], proposal_id)
            self.assertEqual(trace['source_benchmark_scores'], benchmark_score)
            self.assertEqual(trace['oracle_validation'], oracle_result)
            self.assertEqual(trace['human_constraints_applied'], human_constraints)
            
            # Verify the specific requirement: "Authority Trace" and metric value
            self.assertIn('gsm8k', trace['source_benchmark_scores'])
            self.assertEqual(trace['source_benchmark_scores']['gsm8k'], 0.85)

    def test_log_authority_trace_content_verification(self):
        """Verify that the log contains the specific 'Authority Trace' marker and metric value."""
        logger = init_cycle_logger(1)
        log_path = get_log_path(1)
        
        log_authority_trace(
            logger, 
            "prop_456", 
            {"gsm8k": 0.92}, 
            {"passed": True}, 
            {"limit": 0.30}
        )
        
        with open(log_path, 'r') as f:
            content = f.read()
            # The JSON key 'authority_trace' should be present
            self.assertIn('authority_trace', content)
            # The specific metric value should be present
            self.assertIn('0.92', content)
            # The constraint value should be present
            self.assertIn('0.30', content)

if __name__ == '__main__':
    unittest.main()