"""
Tests for T009: Environment configuration and logging infrastructure.
"""
import os
import yaml
import logging
import tempfile
import shutil
from pathlib import Path
import unittest
import sys

# Add parent directory to path to import utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_handler import load_config, setup_logger, log_metric

class TestLoggingInfrastructure(unittest.TestCase):
    
    def setUp(self):
        """Set up a temporary directory for test artifacts."""
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "test_config.yaml")
        self.log_path = os.path.join(self.test_dir, "test.log")
        
        # Create a minimal valid config for testing
        test_config = {
            "logging": {
                "level": "INFO",
                "file_path": self.log_path,
                "format": "%(message)s"
            },
            "default_experiment": {
                "reward_fidelity_level": "dense"
            }
        }
        
        with open(self.config_path, 'w') as f:
            yaml.dump(test_config, f)

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)

    def test_config_yaml_exists(self):
        """Test that config.yaml exists and is valid YAML."""
        # This test verifies the file exists in the project root
        # For the actual project run, we check the real file
        if os.path.exists("config.yaml"):
            with open("config.yaml", 'r') as f:
                try:
                    config = yaml.safe_load(f)
                    self.assertIn('logging', config)
                    self.assertIn('default_experiment', config)
                except yaml.YAMLError:
                    self.fail("config.yaml is not valid YAML")
        else:
            # If running in a temp environment without the real file, skip or assert existence
            self.skipTest("config.yaml not present in current working directory (expected in project root)")

    def test_logger_captures_metrics(self):
        """Test that the logger captures structured metrics."""
        logger = setup_logger("test_logger", config={"logging": {"level": "INFO", "file_path": self.log_path}})
        
        # Log a metric
        log_metric(logger, "test_metric", "test_value", extra_data={"key": "val"})
        
        # Flush handlers
        for handler in logger.handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        
        # Read file
        with open(self.log_path, 'r') as f:
            content = f.read()
        
        # Verify content
        self.assertIn("test_metric=test_value", content)
        self.assertIn("key=val", content)

    def test_default_fidelity_in_config(self):
        """Test that the default config contains the required fidelity level."""
        # Check the actual project config
        if os.path.exists("config.yaml"):
            config = load_config()
            fidelity = config.get('default_experiment', {}).get('reward_fidelity_level')
            self.assertEqual(fidelity, "dense", "Default reward_fidelity_level must be 'dense'")
        else:
            self.skipTest("config.yaml not present")

if __name__ == '__main__':
    unittest.main()