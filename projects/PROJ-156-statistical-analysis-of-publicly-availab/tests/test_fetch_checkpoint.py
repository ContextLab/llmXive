import unittest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.fetch_data import main, load_config
from scripts.utils.checkpoint import load_checkpoint, save_checkpoint, get_checkpoint_path, delete_checkpoint
from llmxive_toolkit import paths

class TestFetchCheckpoint(unittest.TestCase):
    def setUp(self):
        self.checkpoint_path = get_checkpoint_path("fetch_checkpoint.json")
        # Ensure clean state
        delete_checkpoint(self.checkpoint_path)
        
        # Create a mock config.yaml
        self.config_path = paths.code("config.yaml")
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            f.write("games:\n  - game1\n  - game2\n  - game3")

    def tearDown(self):
        delete_checkpoint(self.checkpoint_path)
        if self.config_path.exists():
            os.remove(self.config_path)

    @patch('scripts.fetch_data.fetch_game_runs')
    @patch('scripts.fetch_data.save_raw_data')
    def test_checkpoint_creation(self, mock_save, mock_fetch):
        """Verify that checkpoints are created after each game download."""
        mock_fetch.return_value = [{"id": "run1"}]
        
        # Run main
        main()
        
        checkpoint = load_checkpoint(self.checkpoint_path)
        self.assertIsNotNone(checkpoint)
        self.assertEqual(set(checkpoint['completed_games']), {"game1", "game2", "game3"})

    @patch('scripts.fetch_data.fetch_game_runs')
    @patch('scripts.fetch_data.save_raw_data')
    def test_resumption_logic(self, mock_save, mock_fetch):
        """Verify that the script resumes from the last completed game."""
        # Simulate partial completion
        save_checkpoint({"completed_games": ["game1"]}, self.checkpoint_path)
        
        mock_fetch.return_value = [{"id": "run1"}]
        
        main()
        
        # fetch_game_runs should only be called for game2 and game3
        called_games = [call.args[0] for call in mock_fetch.call_args_list]
        self.assertNotIn("game1", called_games)
        self.assertIn("game2", called_games)
        self.assertIn("game3", called_games)
        self.assertEqual(len(called_games), 2)

    def test_empty_config_failure(self):
        """Verify script handles empty games list gracefully."""
        with open(self.config_path, 'w') as f:
            f.write("games: []")
        
        with self.assertRaises(SystemExit) as cm:
            main()
        self.assertEqual(cm.exception.code, 1)

if __name__ == '__main__':
    unittest.main()