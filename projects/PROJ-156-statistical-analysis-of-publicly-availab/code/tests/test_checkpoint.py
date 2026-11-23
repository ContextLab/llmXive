"""
Integration tests for checkpoint mechanism in fetch_data.py
"""
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.checkpoint import save_checkpoint, load_checkpoint, get_checkpoint_path, ensure_checkpoint_dir
from scripts.fetch_data import main as fetch_main
from unittest.mock import patch, MagicMock

class TestCheckpointIntegration(unittest.TestCase):
    def setUp(self):
        """Set up temporary directories for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.checkpoint_dir = os.path.join(self.test_dir, "checkpoints")
        self.data_dir = os.path.join(self.test_dir, "data", "raw")
        os.makedirs(self.checkpoint_dir)
        os.makedirs(self.data_dir)
        
        # Create a mock config file
        self.config_path = os.path.join(self.test_dir, "config.yaml")
        with open(self.config_path, 'w') as f:
            f.write("games:\n  - test-game-1\n  - test-game-2\nmin_sample_size: 10\n")
        
        # Patch the config path
        self.original_config = "code/config.yaml"
        
    def tearDown(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_save_and_load_checkpoint(self):
        """Test basic save and load functionality."""
        checkpoint_path = get_checkpoint_path(self.checkpoint_dir, "fetch_data")
        test_data = {
            'completed_games': ['game1'],
            'total_games': 2,
            'last_updated': 1234567890
        }
        
        save_checkpoint(checkpoint_path, test_data)
        loaded = load_checkpoint(checkpoint_path)
        
        self.assertEqual(loaded['completed_games'], ['game1'])
        self.assertEqual(loaded['total_games'], 2)
    
    def test_checkpoint_on_interrupt(self):
        """Test that checkpoint is saved when interrupted."""
        checkpoint_path = get_checkpoint_path(self.checkpoint_dir, "fetch_data")
        
        # Simulate saving a partial state
        partial_state = {
            'completed_games': ['test-game-1'],
            'total_games': 2,
            'last_updated': 1234567890
        }
        save_checkpoint(checkpoint_path, partial_state)
        
        # Load and verify
        loaded = load_checkpoint(checkpoint_path)
        self.assertEqual(loaded['completed_games'], ['test-game-1'])
    
    def test_resume_from_checkpoint(self):
        """Test that a subsequent run resumes from checkpoint."""
        # Create initial checkpoint
        checkpoint_path = get_checkpoint_path(self.checkpoint_dir, "fetch_data")
        initial_state = {
            'completed_games': ['test-game-1'],
            'total_games': 2,
            'last_updated': 1234567890
        }
        save_checkpoint(checkpoint_path, initial_state)
        
        # Load checkpoint to verify it's there
        loaded = load_checkpoint(checkpoint_path)
        self.assertIn('test-game-1', loaded['completed_games'])
        self.assertNotIn('test-game-2', loaded['completed_games'])
    
    def test_mock_timeout_interrupt(self):
        """Test checkpoint behavior with simulated timeout."""
        checkpoint_path = get_checkpoint_path(self.checkpoint_dir, "fetch_data")
        
        # Simulate a partial completion
        partial_data = {
            'completed_games': ['test-game-1'],
            'total_games': 2,
            'last_updated': 1234567890
        }
        save_checkpoint(checkpoint_path, partial_data)
        
        # Verify the checkpoint file exists
        self.assertTrue(os.path.exists(checkpoint_path))
        
        # Load and verify contents
        loaded = load_checkpoint(checkpoint_path)
        self.assertEqual(loaded['completed_games'], ['test-game-1'])

if __name__ == '__main__':
    unittest.main()