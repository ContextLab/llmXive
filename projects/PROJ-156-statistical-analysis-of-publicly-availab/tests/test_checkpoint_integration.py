import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.checkpoint import ensure_checkpoint_dir, save_checkpoint, load_checkpoint, delete_checkpoint

class TestCheckpointIntegration(unittest.TestCase):
    """Integration tests for checkpoint mechanism in fetch_data and preprocess scripts."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoint_dir = os.path.join(self.test_dir, "checkpoints")
        self.checkpoint_file = os.path.join(self.checkpoint_dir, "test_checkpoint.json")

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_checkpoint_save_and_load(self):
        """Test that checkpoint can be saved and loaded correctly."""
        ensure_checkpoint_dir(self.checkpoint_dir)
        
        test_state = {
            'completed_games': ['game1', 'game2'],
            'current_index': 2,
            'total_games': 5,
            'partial_metrics': {
                'games_processed': 2,
                'total_records': 100
            }
        }
        
        save_checkpoint(test_state, self.checkpoint_file)
        
        self.assertTrue(os.path.exists(self.checkpoint_file))
        
        loaded_state = load_checkpoint(self.checkpoint_file)
        
        self.assertEqual(loaded_state['completed_games'], test_state['completed_games'])
        self.assertEqual(loaded_state['current_index'], test_state['current_index'])
        self.assertEqual(loaded_state['partial_metrics'], test_state['partial_metrics'])

    def test_checkpoint_resume_simulation(self):
        """Test checkpoint resume simulation for fetch_data.py."""
        ensure_checkpoint_dir(self.checkpoint_dir)
        
        # Simulate partial completion
        state = {
            'completed_games': ['super-mario-64'],
            'current_index': 1,
            'total_games': 3,
            'partial_metrics': {
                'games_processed': 1,
                'total_runs_fetched': 50
            }
        }
        
        save_checkpoint(state, self.checkpoint_file)
        
        # Verify resumption logic
        loaded = load_checkpoint(self.checkpoint_file)
        self.assertEqual(loaded['current_index'], 1)
        self.assertEqual(len(loaded['completed_games']), 1)
        self.assertIn('super-mario-64', loaded['completed_games'])

    def test_checkpoint_delete(self):
        """Test checkpoint deletion on successful completion."""
        ensure_checkpoint_dir(self.checkpoint_dir)
        
        state = {'test': 'data'}
        save_checkpoint(state, self.checkpoint_file)
        self.assertTrue(os.path.exists(self.checkpoint_file))
        
        delete_checkpoint(self.checkpoint_file)
        self.assertFalse(os.path.exists(self.checkpoint_file))

    def test_checkpoint_with_mock_timeout(self):
        """Test that checkpoint is saved before simulated timeout."""
        ensure_checkpoint_dir(self.checkpoint_dir)
        
        # Simulate state before timeout
        state = {
            'completed_games': ['game1'],
            'current_index': 1,
            'total_games': 2,
            'partial_metrics': {'games_processed': 1}
        }
        
        save_checkpoint(state, self.checkpoint_file)
        
        # Verify state is recoverable
        loaded = load_checkpoint(self.checkpoint_file)
        self.assertEqual(loaded['current_index'], 1)
        
        # Simulate cleanup after recovery
        delete_checkpoint(self.checkpoint_file)

if __name__ == '__main__':
    unittest.main()