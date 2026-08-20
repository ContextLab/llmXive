"""
Unit tests for T016b: aggregate_vs_activation.py
"""
import os
import sys
import unittest
import tempfile
import shutil
import csv
from pathlib import Path
import numpy as np

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from aggregate_vs_activation import (
    calculate_mean_activation,
    write_activation_csv,
    find_valid_subject_dirs
)

class TestCalculateMeanActivation(unittest.TestCase):
    
    def test_mean_calculation(self):
        """Test basic mean calculation."""
        ts = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = calculate_mean_activation(ts)
        self.assertAlmostEqual(result, 3.0)

    def test_negative_values(self):
        """Test with negative values."""
        ts = np.array([-1.0, -2.0, -3.0])
        result = calculate_mean_activation(ts)
        self.assertAlmostEqual(result, -2.0)

    def test_single_value(self):
        """Test with a single value."""
        ts = np.array([42.0])
        result = calculate_mean_activation(ts)
        self.assertAlmostEqual(result, 42.0)

    def test_empty_array_raises(self):
        """Test that empty array raises ValueError."""
        ts = np.array([])
        with self.assertRaises(ValueError):
            calculate_mean_activation(ts)

class TestWriteActivationCsv(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = Path(self.temp_dir) / "test_output.csv"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_write_csv(self):
        """Test writing results to CSV."""
        results = [
            {"subject_id": "sub_001", "mean_activation": 1.5},
            {"subject_id": "sub_002", "mean_activation": 2.5}
        ]
        write_activation_csv(results, self.output_path)
        
        self.assertTrue(self.output_path.exists())
        
        with open(self.output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['subject_id'], 'sub_001')
        self.assertAlmostEqual(float(rows[0]['mean_activation']), 1.5)
        self.assertEqual(rows[1]['subject_id'], 'sub_002')

class TestFindValidSubjectDirs(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.processed_dir = Path(self.temp_dir) / "data" / "processed"
        self.processed_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_finds_valid_dirs(self):
        """Test detection of directories with vs_timeseries.npy."""
        # Create valid subject dir
        sub1 = self.processed_dir / "subject_001"
        sub1.mkdir()
        (sub1 / "vs_timeseries.npy").touch()
        
        # Create invalid subject dir (missing file)
        sub2 = self.processed_dir / "subject_002"
        sub2.mkdir()
        
        # Create non-subject dir
        other = self.processed_dir / "other_folder"
        other.mkdir()
        (other / "vs_timeseries.npy").touch()

        found = find_valid_subject_dirs(self.processed_dir)
        
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].name, "subject_001")

    def test_empty_directory(self):
        """Test behavior when no valid dirs exist."""
        found = find_valid_subject_dirs(self.processed_dir)
        self.assertEqual(len(found), 0)

if __name__ == '__main__':
    unittest.main()
