import unittest
import tempfile
import os
import json
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.storage.saver import partition_by_window, compute_checksum, save_partitioned_csvs
from src.data.preprocess.tokenizer import save_tokenized_results, TokenizationResult

class TestSaverLogic(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)
        self.data_dir = self.project_root / "data" / "processed"
        self.data_dir.mkdir(parents=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_partition_by_window_logic(self):
        """Test that records are correctly assigned to 5-year windows."""
        records = [
            {"id": "1", "year": 2002},
            {"id": "2", "year": 2008},
            {"id": "3", "year": 2012},
            {"id": "4", "year": 2017},
            {"id": "5", "year": 2022},
            {"id": "6", "year": 1999}, # Should not be assigned
            {"id": "7", "year": 2025}, # Should not be assigned
        ]

        partitions = partition_by_window(records, window_key="year")

        self.assertEqual(len(partitions["2000-2004"]), 1)
        self.assertEqual(partitions["2000-2004"][0]["id"], "1")

        self.assertEqual(len(partitions["2005-2009"]), 1)
        self.assertEqual(partitions["2005-2009"][0]["id"], "2")

        self.assertEqual(len(partitions["2010-2014"]), 1)
        self.assertEqual(partitions["2010-2014"][0]["id"], "3")

        self.assertEqual(len(partitions["2015-2019"]), 1)
        self.assertEqual(partitions["2015-2019"][0]["id"], "4")

        self.assertEqual(len(partitions["2020-2024"]), 1)
        self.assertEqual(partitions["2020-2024"][0]["id"], "5")

        # Verify unassigned records are not in any window
        for window, recs in partitions.items():
            ids_in_window = [r["id"] for r in recs]
            self.assertNotIn("6", ids_in_window)
            self.assertNotIn("7", ids_in_window)

    def test_compute_checksum_consistency(self):
        """Test that the same DataFrame produces the same checksum."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        checksum1 = compute_checksum(df)
        checksum2 = compute_checksum(df)
        self.assertEqual(checksum1, checksum2)

        # Different data should produce different checksum
        df2 = pd.DataFrame({"a": [1, 2, 4], "b": ["x", "y", "z"]})
        checksum3 = compute_checksum(df2)
        self.assertNotEqual(checksum1, checksum3)

    @patch('src.data.storage.saver.load_preprocessed_data')
    def test_save_partitioned_csvs_creates_files(self, mock_load):
        """Test that CSV files are created for each window with data."""
        # Mock data
        mock_records = [
            {"id": "1", "year": 2002, "source": "arxiv", "title": "Test", "abstract": "Test abstract", "tokens": [], "token_count": 5},
            {"id": "2", "year": 2008, "source": "arxiv", "title": "Test", "abstract": "Test abstract", "tokens": [], "token_count": 5},
            {"id": "3", "year": 2012, "source": "arxiv", "title": "Test", "abstract": "Test abstract", "tokens": [], "token_count": 5},
            {"id": "4", "year": 2017, "source": "arxiv", "title": "Test", "abstract": "Test abstract", "tokens": [], "token_count": 5},
            {"id": "5", "year": 2022, "source": "arxiv", "title": "Test", "abstract": "Test abstract", "tokens": [], "token_count": 5},
        ]
        mock_load.return_value = mock_records

        input_path = self.data_dir / "mock_input.jsonl"
        output_dir = self.data_dir / "output"

        result = save_partitioned_csvs(input_path, output_dir)

        # Verify files exist
        self.assertEqual(len(result), 5)
        for window, info in result.items():
            self.assertIn("file_path", info)
            self.assertIn("checksum", info)
            self.assertIn("record_count", info)
            self.assertTrue(Path(info["file_path"]).exists())

            # Verify record count matches
            df = pd.read_csv(info["file_path"])
            self.assertEqual(len(df), info["record_count"])
            self.assertEqual(info["record_count"], 1) # Based on mock data

    @patch('src.data.storage.saver.load_preprocessed_data')
    def test_save_partitioned_csvs_empty_window(self, mock_load):
        """Test handling of windows with no records."""
        mock_records = [
            {"id": "1", "year": 2002, "source": "arxiv", "title": "Test", "abstract": "Test abstract", "tokens": [], "token_count": 5},
        ]
        mock_load.return_value = mock_records

        input_path = self.data_dir / "mock_input.jsonl"
        output_dir = self.data_dir / "output"

        result = save_partitioned_csvs(input_path, output_dir)

        # Only one window should have data
        self.assertEqual(len(result), 1)
        self.assertIn("2000-2004", result)

if __name__ == "__main__":
    unittest.main()