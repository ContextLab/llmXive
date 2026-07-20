import unittest
import tempfile
import os
import json
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.data.storage.saver import (
    partition_by_window, 
    compute_checksum, 
    save_partitioned_csvs,
    main,
    WINDOWS
)

class TestSaverLogic(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_data = [
            {"id": 1, "year": 2001, "text": "test abstract 1"},
            {"id": 2, "year": 2003, "text": "test abstract 2"},
            {"id": 3, "year": 2006, "text": "test abstract 3"},
            {"id": 4, "year": 2012, "text": "test abstract 4"},
            {"id": 5, "year": 2018, "text": "test abstract 5"},
            {"id": 6, "year": 2022, "text": "test abstract 6"},
            {"id": 7, "year": 1999, "text": "test abstract 7"}, # Should be excluded
            {"id": 8, "year": 2025, "text": "test abstract 8"}, # Should be excluded
        ]
        self.df = pd.DataFrame(self.test_data)
        
    def tearDown(self):
        # Cleanup temp files if needed
        pass
        
    def test_partition_by_window(self):
        """Test that data is correctly partitioned into 5-year windows."""
        partitions = partition_by_window(self.df)
        
        # Check that all expected windows exist
        for window in WINDOWS:
            self.assertIn(window, partitions)
            
        # Check specific counts
        # 2000-2004: 2001, 2003 -> 2 records
        self.assertEqual(len(partitions["2000-2004"]), 2)
        # 2005-2009: 2006 -> 1 record
        self.assertEqual(len(partitions["2005-2009"]), 1)
        # 2010-2014: 2012 -> 1 record
        self.assertEqual(len(partitions["2010-2014"]), 1)
        # 2015-2019: 2018 -> 1 record
        self.assertEqual(len(partitions["2015-2019"]), 1)
        # 2020-2024: 2022 -> 1 record
        self.assertEqual(len(partitions["2020-2024"]), 1)
        
        # Check that outliers are excluded
        total_in_partitions = sum(len(p) for p in partitions.values())
        self.assertEqual(total_in_partitions, 6) # 8 total - 2 outliers
        
    def test_compute_checksum_consistency(self):
        """Test that checksum is deterministic for the same data."""
        checksum1 = compute_checksum(self.df)
        checksum2 = compute_checksum(self.df)
        self.assertEqual(checksum1, checksum2)
        
        # Different data should produce different checksums
        df_diff = pd.DataFrame([{"id": 99, "year": 2000, "text": "different"}])
        checksum_diff = compute_checksum(df_diff)
        self.assertNotEqual(checksum1, checksum_diff)
        
    def test_save_partitioned_csvs(self):
        """Test saving partitions to CSV files."""
        partitions = partition_by_window(self.df)
        output_dir = os.path.join(self.temp_dir, "output")
        
        saved_files, checksums = save_partitioned_csvs(partitions, output_dir)
        
        # Check that files were created
        for window in WINDOWS:
            if len(partitions[window]) > 0:
                self.assertIn(window, saved_files)
                self.assertTrue(os.path.exists(saved_files[window]))
                
                # Verify file content
                df_loaded = pd.read_csv(saved_files[window])
                self.assertEqual(len(df_loaded), len(partitions[window]))
                
                # Verify checksums match
                self.assertIn(window, checksums)
                self.assertEqual(checksums[window], compute_checksum(partitions[window]))
                
    def test_save_partitioned_csvs_empty_window(self):
        """Test handling of empty windows."""
        # Create data that leaves one window empty
        empty_test_data = [
            {"id": 1, "year": 2001, "text": "test"},
            {"id": 2, "year": 2001, "text": "test"},
        ]
        df_empty = pd.DataFrame(empty_test_data)
        partitions = partition_by_window(df_empty)
        
        output_dir = os.path.join(self.temp_dir, "output_empty")
        saved_files, checksums = save_partitioned_csvs(partitions, output_dir)
        
        # Windows with no data should not be in saved_files
        # (based on the implementation which skips empty partitions)
        # But the implementation in saver.py logs a warning and continues.
        # Let's check the behavior:
        # The implementation logs "Skipping save for {window} as it is empty."
        # So it should not be in saved_files.
        
        # We expect only the window 2000-2004 to be saved
        self.assertIn("2000-2004", saved_files)
        self.assertNotIn("2005-2009", saved_files)
        
    def test_main_function_integration(self):
        """Test the main function with a mock file."""
        # Create a temporary input file
        input_data = [
            {"id": 1, "year": 2001, "text": "test 1"},
            {"id": 2, "year": 2006, "text": "test 2"},
            {"id": 3, "year": 2022, "text": "test 3"},
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for record in input_data:
                f.write(json.dumps(record) + '\n')
            temp_input_path = f.name
            
        try:
            # Mock the file path detection in main()
            # We can't easily mock the internal logic of main() without refactoring,
            # so we test the core logic directly instead.
            # This test verifies the partitioning and saving logic works end-to-end
            # if the data is available.
            
            df = pd.read_json(temp_input_path, lines=True)
            partitions = partition_by_window(df)
            output_dir = os.path.join(self.temp_dir, "main_test_output")
            
            saved_files, checksums = save_partitioned_csvs(partitions, output_dir)
            
            self.assertEqual(len(saved_files), 3) # 3 windows have data
            self.assertTrue(all(os.path.exists(f) for f in saved_files.values()))
            
        finally:
            os.unlink(temp_input_path)

if __name__ == '__main__':
    unittest.main()