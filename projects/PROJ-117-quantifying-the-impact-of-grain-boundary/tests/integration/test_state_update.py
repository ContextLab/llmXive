"""
Integration tests for state update functionality.

These tests verify that the state update process works correctly
in a realistic scenario with actual files and directories.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase
import sys
import hashlib

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.update_state import (
    compute_sha256,
    scan_directory,
    load_state,
    save_state,
    verify_hashes,
    main
)


class TestStateUpdateIntegration(TestCase):
    """Integration tests for the state update pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create directory structure similar to project
        dirs = [
            "data/raw",
            "data/processed",
            "models",
            "artifacts/reports",
            "artifacts/figures"
        ]
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)
        
        # Create some test files
        (Path("data/raw") / "sample.json").write_text('{"key": "value"}')
        (Path("data/processed") / "cleaned.parquet").write_bytes(b"fake parquet data")
        (Path("models") / "model.json").write_text('{"model": "data"}')
        (Path("artifacts/reports") / "metrics.json").write_text('{"r2": 0.85}')
        (Path("artifacts/figures") / "plot.png").write_bytes(b"fake png data")
        
        # Create metadata file
        (Path("data") / "metadata.yaml").write_text('source: test')
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_full_state_update_cycle(self):
        """Test complete state update cycle."""
        # Initial state should be empty or default
        state_file = Path("state.yaml")
        
        # Run main
        main()
        
        # Verify state file was created
        self.assertTrue(state_file.exists())
        
        # Load and verify state content
        state = load_state(state_file)
        
        self.assertIn("last_updated", state)
        self.assertIn("artifacts", state)
        self.assertIn("pipeline_runs", state)
        
        # Verify artifacts are tracked
        artifacts = state["artifacts"]
        self.assertGreater(len(artifacts), 0)
        
        # Verify specific files are tracked
        self.assertIn("data/raw/sample.json", artifacts)
        self.assertIn("models/model.json", artifacts)
        self.assertIn("artifacts/reports/metrics.json", artifacts)
        
        # Verify hashes are correct
        for file_path, expected_hash in artifacts.items():
            full_path = Path(file_path)
            actual_hash = compute_sha256(full_path)
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for {file_path}")
    
    def test_state_update_detects_changes(self):
        """Test that state update correctly detects changes."""
        state_file = Path("state.yaml")
        
        # First run - capture initial state
        main()
        initial_state = load_state(state_file)
        initial_artifacts = initial_state["artifacts"].copy()
        
        # Modify a file
        (Path("models") / "model.json").write_text('{"model": "modified"}')
        
        # Add a new file
        (Path("data/processed") / "new_file.json").write_text('{"new": "data"}')
        
        # Delete a file
        (Path("data/raw") / "sample.json").unlink()
        
        # Second run
        main()
        
        # Load updated state
        updated_state = load_state(state_file)
        updated_artifacts = updated_state["artifacts"]
        
        # Verify changes detected
        changes = verify_hashes(updated_artifacts, initial_artifacts)
        
        self.assertIn("data/processed/new_file.json", changes['added'])
        self.assertIn("models/model.json", changes['modified'])
        self.assertIn("data/raw/sample.json", changes['deleted'])
        
        # Verify pipeline_runs updated
        self.assertEqual(len(updated_state["pipeline_runs"]), 2)
        self.assertEqual(updated_state["pipeline_runs"][1]["changes"]["added_count"], 1)
        self.assertEqual(updated_state["pipeline_runs"][1]["changes"]["modified_count"], 1)
        self.assertEqual(updated_state["pipeline_runs"][1]["changes"]["deleted_count"], 1)
    
    def test_state_persistence(self):
        """Test that state persists across multiple runs."""
        state_file = Path("state.yaml")
        
        # Run twice
        main()
        main()
        
        # Load state
        state = load_state(state_file)
        
        # Verify two pipeline runs recorded
        self.assertEqual(len(state["pipeline_runs"]), 2)
        
        # Verify timestamps are different
        timestamps = [run["timestamp"] for run in state["pipeline_runs"]]
        self.assertEqual(len(set(timestamps)), 2)  # All unique
    
    def test_state_with_missing_directories(self):
        """Test state update when some artifact directories are missing."""
        # Remove some directories
        import shutil
        shutil.rmtree("data/raw")
        shutil.rmtree("models")
        
        # Should not fail
        main()
        
        # State should still be created
        state_file = Path("state.yaml")
        self.assertTrue(state_file.exists())
        
        state = load_state(state_file)
        self.assertIn("artifacts", state)
        # Should only have files from existing directories
        self.assertGreater(len(state["artifacts"]), 0)