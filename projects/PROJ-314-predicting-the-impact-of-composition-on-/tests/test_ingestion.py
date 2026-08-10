import unittest
import json
from pathlib import Path
from code.ingestion import fetch_nist_data

class TestIngestion(unittest.TestCase):

    def test_fetch_nist_data(self):
        # Create a dummy file to simulate the existence of data before fetching
        if Path("data/raw/nist_raw.json").exists():
            Path("data/raw/nist_raw.json").unlink()  # Remove if exists

        try:
            fetch_nist_data()
            # Assert that the file is created and contains valid JSON data
            self.assertTrue(Path("data/raw/nist_raw.json").exists())
            with open("data/raw/nist_raw.json", "r") as f:
                data = json.load(f)
                self.assertIsInstance(data, list)
                # Add more specific assertions about the data structure if needed

        except Exception as e:
            self.fail(f"fetch_nist_data() raised an exception: {e}")