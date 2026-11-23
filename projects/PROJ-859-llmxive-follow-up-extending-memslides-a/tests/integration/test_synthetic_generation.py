import unittest
import json
from pathlib import Path

class TestSyntheticGeneration(unittest.TestCase):
    def test_session_files_exist(self):
        data_dir = Path("data/raw")
        session_files = list(data_dir.glob("session_*.json"))
        self.assertTrue(len(session_files) > 0, "No session files found in data/raw/")

    def test_session_file_schema(self):
        data_dir = Path("data/raw")
        session_files = list(data_dir.glob("session_*.json"))
        for file in session_files:
            with open(file, "r") as f:
                try:
                    data = json.load(f)
                    self.assertIn("exact_tool_sequence", data, "Missing 'exact_tool_sequence' key")
                    self.assertIn("raw_arg_variance", data, "Missing 'raw_arg_variance' key")
                except json.JSONDecodeError:
                    self.fail(f"Failed to decode JSON in {file}")
