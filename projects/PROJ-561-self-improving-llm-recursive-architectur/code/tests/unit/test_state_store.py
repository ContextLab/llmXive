import unittest
import os
import sys
import json
import time
import subprocess
import signal
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.state_store import (
    load_state, save_state, update_retry_count, update_mod_history,
    update_degradation_flag, _get_state_path, reset_state
)
from config import get_config, set_config, PathConfig

class TestStateStorePersistence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "state.json")
        # Mock config to use temp dir
        self.original_path = get_config().trajectory_path
        # We need to patch the config or the module's internal path resolution
        # Since _get_state_path relies on get_config().trajectory_path, we'll
        # create a custom config or monkey-patch.
        # Simpler: just set the global in state_store if possible, but it's not exposed.
        # Instead, we will run the test by manipulating the file directly in a temp location
        # and verifying the schema.
        
        # Override the path resolution for this test by patching the module
        import utils.state_store as ss_module
        self.original_get_path = ss_module._get_state_path
        
        def mock_get_path():
            return self.state_file
        
        ss_module._get_state_path = mock_get_path

    def tearDown(self):
        import utils.state_store as ss_module
        ss_module._get_state_path = self.original_get_path
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initial_state_schema(self):
        """Verify initial state has correct schema."""
        state = load_state()
        self.assertIn("cycle_number", state)
        self.assertIn("retry_count", state)
        self.assertIn("mod_history", state)
        self.assertIn("degradation_flag", state)
        self.assertIsInstance(state["cycle_number"], int)
        self.assertIsInstance(state["retry_count"], int)
        self.assertIsInstance(state["mod_history"], list)
        self.assertIsInstance(state["degradation_flag"], bool)

    def test_save_and_load(self):
        """Verify state persists correctly."""
        test_state = {
            "cycle_number": 5,
            "retry_count": 2,
            "mod_history": [{"id": "test"}],
            "degradation_flag": True
        }
        save_state(test_state)
        loaded = load_state()
        self.assertEqual(loaded["cycle_number"], 5)
        self.assertEqual(loaded["retry_count"], 2)
        self.assertEqual(loaded["degradation_flag"], True)
        self.assertEqual(len(loaded["mod_history"]), 1)

    def test_update_retry_count(self):
        """Verify retry count increments."""
        save_state({"cycle_number": 0, "retry_count": 0, "mod_history": [], "degradation_flag": False})
        state = update_retry_count("mod_123")
        self.assertEqual(state["retry_count"], 1)
        self.assertEqual(len(state["mod_history"]), 1)
        self.assertEqual(state["mod_history"][0]["mod_id"], "mod_123")

    def test_update_mod_history(self):
        """Verify mod history appends."""
        save_state({"cycle_number": 0, "retry_count": 0, "mod_history": [], "degradation_flag": False})
        state = update_mod_history("mod_456", {"type": "add_layer"})
        self.assertEqual(len(state["mod_history"]), 1)
        self.assertEqual(state["mod_history"][0]["details"]["type"], "add_layer")

    def test_update_degradation_flag(self):
        """Verify degradation flag updates."""
        save_state({"cycle_number": 0, "retry_count": 0, "mod_history": [], "degradation_flag": False})
        state = update_degradation_flag(True)
        self.assertTrue(state["degradation_flag"])
        self.assertIn("degradation_cycle", state)

    def test_subprocess_survival(self):
        """
        Verify state survives process restart.
        Spawns a worker process to write state, kills it, then reads from a new process.
        """
        worker_script = f"""
import sys
import os
import json
import time

# Setup path
project_root = '{str(project_root / "code")}'
sys.path.insert(0, project_root)

from utils.state_store import save_state, load_state

# Write state
state = {{
    "cycle_number": 99,
    "retry_count": 5,
    "mod_history": [{{"id": "kill_me"}}],
    "degradation_flag": True
}}
save_state(state)

# Sleep to allow kill signal
time.sleep(10)
"""
        worker_proc = subprocess.Popen(
            [sys.executable, "-c", worker_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for file to be written (polling)
        timeout = 5.0
        start = time.time()
        while not os.path.exists(self.state_file):
            if time.time() - start > timeout:
                worker_proc.kill()
                self.fail("State file not created in time")
            time.sleep(0.1)
        
        # Verify content before kill
        with open(self.state_file, 'r') as f:
            content = json.load(f)
        self.assertEqual(content["cycle_number"], 99)

        # Force terminate
        worker_proc.send_signal(signal.SIGKILL)
        worker_proc.wait()

        # Read from "new" process (simulated by just reading file in current context)
        # Since we can't easily spawn a new process that imports the modified module 
        # without complex setup, we verify the file on disk directly as the "new process" would.
        loaded = load_state()
        self.assertEqual(loaded["cycle_number"], 99)
        self.assertEqual(loaded["retry_count"], 5)
        self.assertTrue(loaded["degradation_flag"])
        self.assertEqual(len(loaded["mod_history"]), 1)

if __name__ == '__main__':
    unittest.main()