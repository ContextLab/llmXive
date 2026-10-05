import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
import json
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.fetch_data import main, load_config, save_raw_data
from scripts.utils.checkpoint import load_checkpoint, get_checkpoint_path

class TestFetchCheckpoint(unittest.TestCase):
    def setUp(self):
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.data_raw_dir = Path(self.temp_dir) / "data" / "raw"
        self.data_checkpoints_dir = Path(self.temp_dir) / "data" / "checkpoints"
        self.code_logs_dir = Path(self.temp_dir) / "code" / "logs"
        self.config_dir = Path(self.temp_dir) / "code"

        self.data_raw_dir.mkdir(parents=True)
        self.data_checkpoints_dir.mkdir(parents=True)
        self.code_logs_dir.mkdir(parents=True)
        self.config_dir.mkdir(parents=True)

        # Create a minimal config
        config_content = """
        games:
          - "super-mario-64"
          - "zelda-oot"
          - "metroid-prime"
        min_sample_size: 100
        salt: "test-salt"
        effect_size_assumptions: 0.5
        """
        with open(self.config_dir / "config.yaml", 'w') as f:
            f.write(config_content)

        # Mock the project root
        self.original_project_root = None
        # We'll patch the paths in the module

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('scripts.fetch_data.PROJECT_ROOT')
    @patch('scripts.fetch_data.DATA_RAW_DIR')
    @patch('scripts.fetch_data.DATA_CHECKPOINTS_DIR')
    @patch('scripts.fetch_data.CODE_LOGS_DIR')
    @patch('scripts.fetch_data.load_config')
    @patch('scripts.fetch_data.fetch_game_runs')
    @patch('scripts.fetch_data.save_raw_data')
    def test_checkpoint_creation_and_resumption(self, mock_save_raw, mock_fetch, mock_load_config,
                                                mock_logs_dir, mock_cp_dir, mock_raw_dir, mock_project_root):
        """Test that checkpoint is created and resumption works"""
        # Setup mocks
        mock_project_root.__truediv__ = lambda self, other: Path(self.temp_dir) / other
        mock_raw_dir.__truediv__ = lambda self, other: self.data_raw_dir / other
        mock_cp_dir.__truediv__ = lambda self, other: self.data_checkpoints_dir / other
        mock_logs_dir.__truediv__ = lambda self, other: self.code_logs_dir / other

        mock_load_config.return_value = {
            'games': ['super-mario-64', 'zelda-oot', 'metroid-prime'],
            'min_sample_size': 100
        }

        # Mock fetch_game_runs to return sample data
        mock_fetch.side_effect = [
            [{'id': 'run1', 'times': {'raw': 100}}],  # First game
            [{'id': 'run2', 'times': {'raw': 200}}],  # Second game
            [{'id': 'run3', 'times': {'raw': 300}}]   # Third game
        ]

        # Mock save_raw_data to do nothing but log
        def mock_save(game_id, runs):
            output_path = self.data_raw_dir / f"raw_{game_id}.json"
            with open(output_path, 'w') as f:
                json.dump(runs, f)

        mock_save_raw.side_effect = mock_save

        # First run: simulate interruption after first game
        with patch('scripts.fetch_data.logger') as mock_logger:
            # Simulate KeyboardInterrupt after first game
            original_fetch = mock_fetch.side_effect
            def interrupt_after_first(*args, **kwargs):
                result = original_fetch[0](*args, **kwargs)
                raise KeyboardInterrupt("Simulated timeout")

            mock_fetch.side_effect = interrupt_after_first

            try:
                main()
            except KeyboardInterrupt:
                pass  # Expected

            # Verify checkpoint was created
            checkpoint_path = get_checkpoint_path(self.data_checkpoints_dir, "fetch_data")
            self.assertTrue(checkpoint_path.exists(), "Checkpoint file should be created after interruption")

            checkpoint_data = load_checkpoint(checkpoint_path)
            self.assertIn('completed_games', checkpoint_data)
            self.assertEqual(len(checkpoint_data['completed_games']), 1)
            self.assertEqual(checkpoint_data['next_game_index'], 1)

        # Second run: verify resumption
        mock_fetch.side_effect = [
            [{'id': 'run2', 'times': {'raw': 200}}],  # Second game
            [{'id': 'run3', 'times': {'raw': 300}}]   # Third game
        ]

        with patch('scripts.fetch_data.logger') as mock_logger:
            main()

            # Verify only remaining games were fetched
            self.assertEqual(mock_fetch.call_count, 2)
            self.assertIn('super-mario-64', [call[0][0] for call in mock_fetch.call_args_list])
            self.assertNotIn('super-mario-64', [call[0][0] for call in mock_fetch.call_args_list])

            # Verify final checkpoint
            checkpoint_data = load_checkpoint(checkpoint_path)
            self.assertEqual(checkpoint_data['status'], 'complete')
            self.assertEqual(len(checkpoint_data['completed_games']), 3)

    @patch('scripts.fetch_data.PROJECT_ROOT')
    @patch('scripts.fetch_data.DATA_RAW_DIR')
    @patch('scripts.fetch_data.DATA_CHECKPOINTS_DIR')
    @patch('scripts.fetch_data.CODE_LOGS_DIR')
    @patch('scripts.fetch_data.load_config')
    @patch('scripts.fetch_data.fetch_game_runs')
    @patch('scripts.fetch_data.save_raw_data')
    def test_no_checkpoint_start_fresh(self, mock_save_raw, mock_fetch, mock_load_config,
                                       mock_logs_dir, mock_cp_dir, mock_raw_dir, mock_project_root):
        """Test that without checkpoint, processing starts from beginning"""
        mock_project_root.__truediv__ = lambda self, other: Path(self.temp_dir) / other
        mock_raw_dir.__truediv__ = lambda self, other: self.data_raw_dir / other
        mock_cp_dir.__truediv__ = lambda self, other: self.data_checkpoints_dir / other
        mock_logs_dir.__truediv__ = lambda self, other: self.code_logs_dir / other

        mock_load_config.return_value = {
            'games': ['super-mario-64', 'zelda-oot'],
            'min_sample_size': 100
        }

        mock_fetch.side_effect = [
            [{'id': 'run1', 'times': {'raw': 100}}],
            [{'id': 'run2', 'times': {'raw': 200}}]
        ]

        def mock_save(game_id, runs):
            output_path = self.data_raw_dir / f"raw_{game_id}.json"
            with open(output_path, 'w') as f:
                json.dump(runs, f)

        mock_save_raw.side_effect = mock_save

        with patch('scripts.fetch_data.logger') as mock_logger:
            main()

            # Verify both games were fetched
            self.assertEqual(mock_fetch.call_count, 2)
            checkpoint_data = load_checkpoint(get_checkpoint_path(self.data_checkpoints_dir, "fetch_data"))
            self.assertEqual(checkpoint_data['next_game_index'], 2)

if __name__ == '__main__':
    unittest.main()