import unittest
import os
import json
from pathlib import Path
from code.state_manager import log_unresolved_realization, get_unresolved_summary, clear_unresolved_log
from code.state_utils import ensure_state_structure, compute_file_checksum, load_project_state, save_project_state, register_artifact, verify_artifact_integrity, get_artifact_summary

class TestStateManager(unittest.TestCase):

    def setUp(self):
        # Ensure state directory exists before each test
        ensure_state_structure()
        # Clear any existing state data
        clear_unresolved_log()
        self.project_name = "PROJ-308-quantifying-entanglement-entropy-in-rand"

    def test_log_and_get_unresolved_realization(self):
        log_unresolved_realization(1, "Convergence failed")
        summary = get_unresolved_summary()
        self.assertEqual(summary["Convergence failed"], 1)

    def test_clear_unresolved_log(self):
        log_unresolved_realization(1, "Convergence failed")
        summary = get_unresolved_summary()
        self.assertEqual(summary["Convergence failed"], 1)
        clear_unresolved_log()
        summary = get_unresolved_summary()
        self.assertEqual(summary, {})

    def test_state_structure(self):
        ensure_state_structure()
        self.assertTrue(Path("state/projects").exists())

    def test_file_checksum(self):
        # Create a temporary file for checksum testing
        temp_file = "temp_checksum_file.txt"
        with open(temp_file, "w") as f:
            f.write("This is a test file.")
        checksum = compute_file_checksum(temp_file)
        self.assertTrue(len(checksum) > 0)
        os.remove(temp_file)

    def test_load_and_save_project_state(self):
        state = {"file1": "checksum1", "file2": "checksum2"}
        save_project_state(self.project_name, state)
        loaded_state = load_project_state(self.project_name)
        self.assertEqual(loaded_state, state)

    def test_register_and_verify_artifact(self):
        artifact_path = "data/entropy_data.csv"
        checksum = "test_checksum"
        register_artifact(self.project_name, artifact_path, checksum)
        self.assertTrue(verify_artifact_integrity(self.project_name, artifact_path))

    def test_artifact_summary(self):
        artifact_path = "data/entropy_data.csv"
        checksum = "test_checksum"
        register_artifact(self.project_name, artifact_path, checksum)
        summary = get_artifact_summary(self.project_name)
        self.assertIn(artifact_path, summary)
        self.assertEqual(summary[artifact_path], checksum)

    def test_checksums(self):
      # Create a dummy file to calculate and check checksums
      dummy_file = "test_checksum.txt"
      with open(dummy_file, "w") as f:
          f.write("This is a test file for checksums.")

      # Calculate the checksum
      checksum = compute_file_checksum(dummy_file)

      # Save the checksum to the state
      save_project_state(self.project_name, {"test_checksum.txt": checksum})

      # Load the state and verify the checksum
      loaded_state = load_project_state(self.project_name)
      self.assertEqual(loaded_state["test_checksum.txt"], checksum)

      # Clean up the dummy file
      os.remove(dummy_file)
