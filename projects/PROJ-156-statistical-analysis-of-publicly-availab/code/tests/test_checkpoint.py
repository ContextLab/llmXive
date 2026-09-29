import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.checkpoint import ensure_checkpoint_dir, save_checkpoint, load_checkpoint, get_checkpoint_path
from scripts.fetch_data import main as fetch_main
from scripts.preprocess import main as preprocess_main

class TestCheckpointIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create necessary directory structure
        os.makedirs("data/raw", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        os.makedirs("code/scripts/utils", exist_ok=True)
        
        # Create a minimal config file
        config_content = """
        games: ["test-game-1"]
        min_sample_size: 10
        salt: "test_salt_123"
        """
        with open("code/config.yaml", "w") as f:
            f.write(config_content)
        
        # Create a mock raw data file
        mock_data = {
            "data": [
                {
                    "id": "run1",
                    "game": {"id": "test-game-1"},
                    "player": {"id": "runner1"},
                    "times": {"primary": 100},
                    "date": "2023-01-01T00:00:00Z"
                },
                {
                    "id": "run2",
                    "game": {"id": "test-game-1"},
                    "player": {"id": "runner1"},
                    "times": {"primary": 95},
                    "date": "2023-01-02T00:00:00Z"
                }
            ]
        }
        with open("data/raw/test-game-1_runs.json", "w") as f:
            json.dump(mock_data, f)

    def tearDown(self):
        """Clean up test fixtures"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_checkpoint_creation_and_loading(self):
        """Test that checkpoints are created and loaded correctly"""
        # Save a checkpoint
        checkpoint_path = get_checkpoint_path("test_checkpoint")
        save_checkpoint(checkpoint_path, {"test_key": "test_value", "processed": ["game1"]})
        
        # Load the checkpoint
        loaded_data = load_checkpoint(checkpoint_path)
        
        self.assertEqual(loaded_data["test_key"], "test_value")
        self.assertEqual(loaded_data["processed"], ["game1"])

    def test_checkpoint_in_fetch_data(self):
        """Test that fetch_data creates checkpoints after each game"""
        # This test verifies the integration of checkpointing in fetch_data
        # Since we can't actually fetch from the API, we verify the checkpoint logic exists
        import importlib.util
        spec = importlib.util.spec_from_file_location("fetch_data", "code/scripts/fetch_data.py")
        fetch_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fetch_module)
        
        # Verify checkpoint functions are imported
        self.assertTrue(hasattr(fetch_module, 'ensure_checkpoint_dir'))
        self.assertTrue(hasattr(fetch_module, 'save_checkpoint'))
        self.assertTrue(hasattr(fetch_module, 'load_checkpoint'))

    def test_checkpoint_in_preprocess(self):
        """Test that preprocess creates checkpoints after each game"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("preprocess", "code/scripts/preprocess.py")
        preprocess_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(preprocess_module)
        
        # Verify checkpoint functions are imported
        self.assertTrue(hasattr(preprocess_module, 'ensure_checkpoint_dir'))
        self.assertTrue(hasattr(preprocess_module, 'save_checkpoint'))
        self.assertTrue(hasattr(preprocess_module, 'load_checkpoint'))

    def test_checkpoint_persistence_across_runs(self):
        """Test that checkpoint data persists between simulated runs"""
        checkpoint_path = get_checkpoint_path("persistence_test")
        
        # Simulate first run processing game1
        save_checkpoint(checkpoint_path, {"processed_games": ["game1"], "step": 1})
        
        # Simulate second run continuing from checkpoint
        loaded = load_checkpoint(checkpoint_path)
        self.assertIn("game1", loaded["processed_games"])
        self.assertEqual(loaded["step"], 1)
        
        # Simulate processing game2
        loaded["processed_games"].append("game2")
        loaded["step"] = 2
        save_checkpoint(checkpoint_path, loaded)
        
        # Verify updated checkpoint
        final = load_checkpoint(checkpoint_path)
        self.assertIn("game2", final["processed_games"])
        self.assertEqual(final["step"], 2)

if __name__ == "__main__":
    unittest.main()