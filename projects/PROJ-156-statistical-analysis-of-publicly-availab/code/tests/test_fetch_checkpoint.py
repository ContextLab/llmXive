"""
Unit tests for the fetch‑data checkpoint integration (task T015a).

The tests verify that:

* The checkpoint file is created after the first successful game.
* Subsequent runs resume without re‑downloading already‑fetched games.
* The checkpoint JSON contains the expected ``completed_games`` list.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Import the script under test
from scripts import fetch_data

class TestFetchCheckpoint(unittest.TestCase):
    def setUp(self):
        # Create an isolated temporary directory for the test run
        self.tmp_dir = tempfile.mkdtemp()
        self.orig_cwd = os.getcwd()
        os.chdir(self.tmp_dir)

        # Minimal config with two dummy games
        config_yaml = """
        games:
          - gameA
          - gameB
        min_sample_size: 10
        random_seed: 42
        """
        os.makedirs("code", exist_ok=True)
        with open("code/config.yaml", "w") as f:
            f.write(config_yaml)

        # Ensure the raw data directory exists (the fetch script writes here)
        os.makedirs("data/raw", exist_ok=True)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        shutil.rmtree(self.tmp_dir)

    @patch.object(fetch_data, "fetch_game_runs")
    @patch.object(fetch_data, "save_raw_data")
    def test_checkpoint_creation_and_resumption(self, mock_save_raw, mock_fetch):
        """
        Simulate a successful download for the first game, then raise
        ``KeyboardInterrupt`` during the second to emulate a crash.
        After restarting, the script should skip the first game and
        process only the remaining one.
        """
        # First call returns dummy data; second call raises to simulate failure
        mock_fetch.side_effect = [
            [{"id": "run1"}],  # data for gameA
            KeyboardInterrupt("simulated interruption")
        ]

        # Run the script – it should abort after the interruption
        with self.assertRaises(SystemExit):
            fetch_data.main()

        # Verify that a checkpoint was written and contains only ``gameA``
        checkpoint_path = Path("data/checkpoints/fetch_checkpoint.json")
        self.assertTrue(checkpoint_path.is_file(), "Checkpoint file not created")
        with checkpoint_path.open() as f:
            ck = json.load(f)
        self.assertIn("completed_games", ck)
        self.assertEqual(ck["completed_games"], ["gameA"])

        # Reset the mock: now both games succeed
        mock_fetch.side_effect = [
            [{"id": "run1"}],  # gameA (should be skipped)
            [{"id": "run2"}],  # gameB
        ]

        # Run the script again – it should resume and only process gameB
        fetch_data.main()

        # Check that ``save_raw_data`` was called exactly twice:
        #   * once for gameA during the first run,
        #   * once for gameB during the resumed run.
        self.assertEqual(mock_save_raw.call_count, 2)

        # The final checkpoint should list both games
        with checkpoint_path.open() as f:
            final_ck = json.load(f)
        self.assertCountEqual(final_ck["completed_games"], ["gameA", "gameB"])

    def test_no_checkpoint_when_all_games_succeed(self):
        """
        When all games are fetched without interruption, the checkpoint
        file should still be created (containing all games) and not be
        removed by the script.
        """
        with patch.object(fetch_data, "fetch_game_runs", return_value=[{"id": "run"}]), \
             patch.object(fetch_data, "save_raw_data"):
            fetch_data.main()

        ck_path = Path("data/checkpoints/fetch_checkpoint.json")
        self.assertTrue(ck_path.is_file())
        with ck_path.open() as f:
            ck = json.load(f)
        self.assertCountEqual(ck["completed_games"], ["gameA", "gameB"])

if __name__ == "__main__":
    unittest.main()