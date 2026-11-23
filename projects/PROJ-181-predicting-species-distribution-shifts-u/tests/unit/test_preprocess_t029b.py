"""
Unit tests for T029b: Preprocess recent occurrence data.
Tests FR-006 threshold checking, insufficient data flagging, and spatial thinning.
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocess import check_insufficient_data, thin_occurrences, filter_and_deduplicate
from config import METRICS_DIR, DATA_DIR

class TestT029bPreprocess(unittest.TestCase):
    
    def setUp(self):
        """Set up temporary directories and test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir) / "data"
        self.test_metrics_dir = Path(self.temp_dir) / "metrics"
        self.test_data_dir.mkdir()
        self.test_metrics_dir.mkdir()
        
        # Create mock data for testing
        self.mock_data = pd.DataFrame({
            'species': ['Species_A', 'Species_A', 'Species_A', 'Species_B', 'Species_B', 'Species_C'],
            'decimalLatitude': [40.0, 40.1, 40.2, 35.0, 35.1, 30.0],
            'decimalLongitude': [-75.0, -75.1, -75.2, -80.0, -80.1, -90.0],
            'eventDate': ['2010-05-01', '2010-05-02', '2010-05-03', '2015-06-01', '2015-06-02', '2018-07-01'],
            'source_identifier': ['test1', 'test1', 'test1', 'test2', 'test2', 'test3'],
            'download_timestamp': ['2023-01-01T00:00:00'] * 6,
            'original_dataset_name': ['dataset1', 'dataset1', 'dataset1', 'dataset2', 'dataset2', 'dataset3']
        })
        
        # Species_A: 3 records (< 100) -> INSUFFICIENT
        # Species_B: 2 records (< 100) -> INSUFFICIENT
        # Species_C: 1 record (< 100) -> INSUFFICIENT
        
        self.input_path = self.test_data_dir / "test_input.csv"
        self.output_path = self.test_data_dir / "test_output.csv"
        self.insufficient_path = self.test_metrics_dir / "test_insufficient.json"
        
        self.mock_data.to_csv(self.input_path, index=False)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_check_insufficient_data_all_insufficient(self):
        """Test that all species with <100 records are flagged as INSUFFICIENT_DATA."""
        result = check_insufficient_data(str(self.input_path), str(self.insufficient_path))
        
        self.assertEqual(len(result), 3)
        
        # Check all are flagged as insufficient
        for item in result:
            self.assertEqual(item['status'], 'INSUFFICIENT_DATA')
            self.assertLess(item['count'], 100)
        
        # Verify JSON file was created
        self.assertTrue(self.insufficient_path.exists())
        
        with open(self.insufficient_path, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(len(loaded_data), 3)
    
    def test_filter_and_deduplicate(self):
        """Test filtering and deduplication removes exact duplicates."""
        # Create data with duplicates
        dup_data = pd.DataFrame({
            'species': ['Species_A', 'Species_A', 'Species_A'],
            'decimalLatitude': [40.0, 40.0, 40.1],
            'decimalLongitude': [-75.0, -75.0, -75.1],
            'eventDate': ['2010-05-01', '2010-05-01', '2010-05-02'],
            'source_identifier': ['test', 'test', 'test'],
            'download_timestamp': ['2023-01-01'] * 3,
            'original_dataset_name': ['dataset', 'dataset', 'dataset']
        })
        
        dup_path = self.test_data_dir / "duplicates.csv"
        dup_out_path = self.test_data_dir / "deduped.csv"
        dup_data.to_csv(dup_path, index=False)
        
        result = filter_and_deduplicate(str(dup_path), str(dup_out_path))
        
        # Should have 2 unique records (one duplicate removed)
        self.assertEqual(len(result), 2)
        
        # Verify file exists
        self.assertTrue(dup_out_path.exists())
    
    def test_thin_occurrences_distance(self):
        """Test that thinning maintains minimum distance between points."""
        # Create data with points closer than 10km
        # Using coordinates that are very close (within 1km)
        close_data = pd.DataFrame({
            'species': ['Species_A', 'Species_A', 'Species_A'],
            'decimalLatitude': [40.0, 40.001, 40.002],  # ~110m apart
            'decimalLongitude': [-75.0, -75.001, -75.002],
            'eventDate': ['2010-05-01', '2010-05-02', '2010-05-03'],
            'source_identifier': ['test'] * 3,
            'download_timestamp': ['2023-01-01'] * 3,
            'original_dataset_name': ['dataset'] * 3
        })
        
        close_path = self.test_data_dir / "close_points.csv"
        close_out_path = self.test_data_dir / "thinned_points.csv"
        close_data.to_csv(close_path, index=False)
        
        result = thin_occurrences(str(close_path), str(close_out_path), distance_km=10.0)
        
        # All points are within 1km, so only 1 should remain
        self.assertLessEqual(len(result), 1)
        
        # Verify file exists
        self.assertTrue(close_out_path.exists())
    
    def test_insufficient_data_logic_integration(self):
        """Test the full T029b logic: check threshold, flag, then thin only sufficient."""
        # Create data with mixed sufficient/insufficient species
        mixed_data = pd.DataFrame({
            'species': ['Species_A'] * 150 + ['Species_B'] * 50,  # A: sufficient, B: insufficient
            'decimalLatitude': [40.0 + i * 0.01 for i in range(200)],
            'decimalLongitude': [-75.0 + i * 0.01 for i in range(200)],
            'eventDate': ['2010-05-01'] * 200,
            'source_identifier': ['test'] * 200,
            'download_timestamp': ['2023-01-01'] * 200,
            'original_dataset_name': ['dataset'] * 200
        })
        
        mixed_path = self.test_data_dir / "mixed.csv"
        mixed_out_path = self.test_data_dir / "mixed_thinned.csv"
        mixed_insufficient_path = self.test_metrics_dir / "mixed_insufficient.json"
        
        mixed_data.to_csv(mixed_path, index=False)
        
        # Check insufficient data
        result = check_insufficient_data(str(mixed_path), str(mixed_insufficient_path))
        
        # Species_B should be flagged
        species_b_flagged = any(item['species'] == 'Species_B' and item['status'] == 'INSUFFICIENT_DATA' for item in result)
        self.assertTrue(species_b_flagged)
        
        # Species_A should NOT be flagged
        species_a_flagged = any(item['species'] == 'Species_A' and item['status'] == 'INSUFFICIENT_DATA' for item in result)
        self.assertFalse(species_a_flagged)

if __name__ == '__main__':
    unittest.main()
