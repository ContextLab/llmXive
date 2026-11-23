import os
import sys
import unittest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.preprocess import main, load_config, setup_logging
from scripts.utils.checkpoint import load_checkpoint, get_checkpoint_path

class TestPreprocessCheckpoint(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create necessary directory structure
        Path("code/logs").mkdir(parents=True, exist_ok=True)
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        Path("data/processed").mkdir(parents=True, exist_ok=True)
        Path("data/checkpoints").mkdir(parents=True, exist_ok=True)
        Path("contracts").mkdir(parents=True, exist_ok=True)
        Path("code").mkdir(parents=True, exist_ok=True)
        
        # Create config file
        config_content = """
        games:
          - "test-game-1"
          - "test-game-2"
        min_sample_size: 10
        salt: "test-salt"
        effect_size_assumptions: 0.5
        """
        with open("code/config.yaml", "w") as f:
            f.write(config_content)
        
        # Create schema file
        schema_content = """
        $schema: http://json-schema.org/draft-07/schema#
        type: object
        properties:
          run_time_seconds: { type: number }
          runner_id: { type: string }
          attempt_number: { type: integer }
          category: { type: string }
          submission_date: { type: string }
          game_id: { type: string }
        required: [run_time_seconds, runner_id, attempt_number, category, submission_date, game_id]
        """
        with open("contracts/run_record.schema.yaml", "w") as f:
            f.write(schema_content)
        
        # Create mock raw data for test-game-1
        mock_data_1 = {
            "runs": [
                {
                    "id": "run1",
                    "runner_id": "runner1",
                    "attempt_number": 1,
                    "category": "any%",
                    "submission_date": "2023-01-01T12:00:00Z",
                    "game_id": "test-game-1",
                    "run_time_seconds": 100.5
                },
                {
                    "id": "run2",
                    "runner_id": "runner2",
                    "attempt_number": 1,
                    "category": "any%",
                    "submission_date": "2023-01-02T12:00:00Z",
                    "game_id": "test-game-1",
                    "run_time_seconds": 95.2
                }
            ]
        }
        with open("data/raw/test-game-1_raw.json", "w") as f:
            json.dump(mock_data_1, f)
        
        # Create mock raw data for test-game-2
        mock_data_2 = {
            "runs": [
                {
                    "id": "run3",
                    "runner_id": "runner1",
                    "attempt_number": 2,
                    "category": "any%",
                    "submission_date": "2023-01-03T12:00:00Z",
                    "game_id": "test-game-2",
                    "run_time_seconds": 88.7
                }
            ]
        }
        with open("data/raw/test-game-2_raw.json", "w") as f:
            json.dump(mock_data_2, f)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def test_checkpoint_creation_after_first_game(self):
        """Test that a checkpoint is created after processing the first game."""
        # Mock the processing of the second game to simulate interruption
        with patch('scripts.preprocess.calculate_lagged_pressure') as mock_calc:
            mock_calc.side_effect = KeyboardInterrupt("Simulated timeout")
            
            # This should raise KeyboardInterrupt after processing first game
            with self.assertRaises(KeyboardInterrupt):
                main()
        
        # Check that checkpoint file exists
        checkpoint_path = get_checkpoint_path("preprocess")
        self.assertTrue(Path(checkpoint_path).exists(), "Checkpoint file should exist after interruption")
        
        # Load and verify checkpoint content
        checkpoint_data = load_checkpoint(checkpoint_path)
        self.assertIsNotNone(checkpoint_data)
        self.assertIn('last_game_idx', checkpoint_data)
        self.assertEqual(checkpoint_data['last_game_idx'], 1, "Should have processed 1 game")
        self.assertIn('processed_runs', checkpoint_data)
        self.assertGreater(len(checkpoint_data['processed_runs']), 0, "Should have processed runs")

    def test_checkpoint_resumption(self):
        """Test that preprocessing resumes from checkpoint correctly."""
        # First, create a checkpoint manually simulating partial processing
        checkpoint_path = get_checkpoint_path("preprocess")
        
        # Create mock data for first game only
        mock_data_1 = {
            "runs": [
                {
                    "id": "run1",
                    "runner_id": "runner1",
                    "attempt_number": 1,
                    "category": "any%",
                    "submission_date": "2023-01-01T12:00:00Z",
                    "game_id": "test-game-1",
                    "run_time_seconds": 100.5
                }
            ]
        }
        with open("data/raw/test-game-1_raw.json", "w") as f:
            json.dump(mock_data_1, f)
        
        # Create checkpoint for first game
        checkpoint_data = {
            'last_game_idx': 1,
            'processed_runs': [mock_data_1['runs'][0]],
            'runner_profiles': {
                'hashed_runner1': {
                    'total_prior_runs': 1,
                    'time_since_first_run_days': 0,
                    'games_played_count': 1
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f)
        
        # Now run main and verify it resumes from game 2
        # We'll mock the second game processing to complete successfully
        with patch('scripts.preprocess.load_raw_data') as mock_load:
            mock_load.return_value = [
                {
                    "id": "run2",
                    "runner_id": "runner2",
                    "attempt_number": 1,
                    "category": "any%",
                    "submission_date": "2023-01-02T12:00:00Z",
                    "game_id": "test-game-2",
                    "run_time_seconds": 95.2
                }
            ]
            
            # Run preprocessing - should start from game 2 (index 1)
            main()
        
        # Verify that the output file contains data from both games
        output_path = Path("data/processed/run_records.csv")
        self.assertTrue(output_path.exists(), "Output file should exist")
        
        with open(output_path, 'r') as f:
            import csv
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Should have 2 runs (1 from checkpoint + 1 from resumed processing)
        self.assertEqual(len(rows), 2, "Should have 2 runs in output")
        
        # Verify checkpoint file was removed after successful completion
        self.assertFalse(Path(checkpoint_path).exists(), "Checkpoint file should be removed after successful completion")

    def test_no_checkpoint_on_successful_run(self):
        """Test that no checkpoint file remains after successful completion."""
        # Ensure all games can be processed without interruption
        main()
        
        # Verify checkpoint file does not exist
        checkpoint_path = get_checkpoint_path("preprocess")
        self.assertFalse(Path(checkpoint_path).exists(), "Checkpoint file should not exist after successful completion")
        
        # Verify output files were created
        self.assertTrue(Path("data/processed/run_records.csv").exists())
        self.assertTrue(Path("data/processed/runner_profiles.csv").exists())

if __name__ == '__main__':
    unittest.main()