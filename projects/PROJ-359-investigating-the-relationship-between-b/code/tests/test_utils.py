"""
Unit tests for code/src/utils.py
"""
import json
import os
import random
import tempfile
from pathlib import Path
from unittest import TestCase, mock

import numpy as np

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from src import utils


class TestSeeding(TestCase):
    def test_seed_manager_default(self):
        """Test that seed_manager uses default if env var is missing."""
        with mock.patch.dict(os.environ, {}, clear=True):
            # Ensure no RANDOM_SEED exists
            if "RANDOM_SEED" in os.environ:
                del os.environ["RANDOM_SEED"]
            
            # We need to reload the module to pick up the env change if it was cached,
            # but for this test we just call the function logic directly.
            # The function reads os.environ directly.
            seed = utils.seed_manager()
            self.assertEqual(seed, utils.DEFAULT_RANDOM_SEED)

    def test_seed_manager_env_var(self):
        """Test that seed_manager respects RANDOM_SEED env var."""
        test_seed = 12345
        with mock.patch.dict(os.environ, {"RANDOM_SEED": str(test_seed)}):
            seed = utils.seed_manager()
            self.assertEqual(seed, test_seed)

    def test_determinism(self):
        """Test that seeding produces deterministic results."""
        utils.seed_manager()
        r1 = random.random()
        n1 = np.random.rand()
        
        utils.seed_manager()
        r2 = random.random()
        n2 = np.random.rand()
        
        self.assertEqual(r1, r2)
        self.assertEqual(n1, n2)


class TestLogging(TestCase):
    def setUp(self):
        """Create a temporary directory for logs."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "pipeline_log.json"
        # Monkey patch get_log_path to use temp dir
        self.original_get_log_path = utils.get_log_path
        utils.get_log_path = lambda: self.log_path

    def tearDown(self):
        """Cleanup temporary directory."""
        self.temp_dir.cleanup()
        utils.get_log_path = self.original_get_log_path
        # Clean up the module's cached log state if any (not applicable here as we reload logic)
        if self.log_path.exists():
            self.log_path.unlink()

    def test_load_existing_log_missing(self):
        """Test loading log when file does not exist."""
        log = utils.load_existing_log()
        self.assertEqual(log["pipeline_status"], "INITIALIZED")
        self.assertIn("logs", log)

    def test_log_event(self):
        """Test appending an event to the log."""
        utils.log_event("INFO", "Test message", data={"key": "value"})
        
        self.assertTrue(self.log_path.exists())
        with open(self.log_path, "r") as f:
            data = json.load(f)
        
        self.assertEqual(len(data["logs"]), 1)
        self.assertEqual(data["logs"][0]["type"], "INFO")
        self.assertEqual(data["logs"][0]["message"], "Test message")
        self.assertEqual(data["logs"][0]["data"], {"key": "value"})

    def test_write_json_log_update(self):
        """Test writing a full log update."""
        utils.write_json_log(
            status="SUCCESS",
            exclusion_motion=5,
            total_runtime_seconds=100.5
        )
        
        with open(self.log_path, "r") as f:
            data = json.load(f)
        
        self.assertEqual(data["pipeline_status"], "SUCCESS")
        self.assertEqual(data["exclusion_motion"], 5)
        self.assertEqual(data["total_runtime_seconds"], 100.5)
        self.assertIn("end_time", data)

    def test_motion_threshold_constant(self):
        """Verify the motion threshold constant is set correctly."""
        self.assertEqual(utils.MOTION_THRESHOLD_MM, 3.0)
