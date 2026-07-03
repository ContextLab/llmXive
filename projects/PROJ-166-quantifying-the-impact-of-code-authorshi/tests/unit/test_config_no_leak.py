import os
import unittest
from unittest.mock import patch
import logging

class TestConfigNoLeak(unittest.TestCase):
    
    @patch.dict(os.environ, {"GITHUB_TOKEN": "secret123", "NVD_API_KEY": "secret456"})
    def test_no_api_key_in_logs(self):
        """Verify that API keys are not logged."""
        import code.config as config
        
        # Capture log output
        with self.assertNoLogs(level=logging.WARNING):
            # Accessing the module shouldn't leak keys
            _ = config.GITHUB_TOKEN
            _ = config.NVD_API_KEY
        
        # Explicit check: ensure keys are not in the module's string representation
        module_str = str(config.__dict__)
        self.assertNotIn("secret123", module_str)
        self.assertNotIn("secret456", module_str)