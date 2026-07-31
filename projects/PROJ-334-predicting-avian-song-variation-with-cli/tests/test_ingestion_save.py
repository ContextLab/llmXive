import os
import sys
import csv
import tempfile
import hashlib
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from ingestion import (
    haversine_distance,
    perform_spatial_join,
    save_processed_data,
    main
)
from data_setup import initialize_checksums_file

class TestIngestionSave(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.raw_song_path = Path(self.temp_dir) / 'raw_song.csv'
        self.raw_climate_path = Path(self.temp_dir) / 'raw_climate.csv'
        self.output_path = Path(self.temp_dir) / 'output_analysis.csv'
        self.checksum_path = Path(self.temp_dir) / 'checksums.txt'

        # Create mock raw data
        song_data = [
            {'species_id': 'sp1', 'lat': 0.0, 'lon': 0.0, 'song_metric_1': 10.0},
            {'species_id': 'sp2', 'lat': 1.0, 'lon': 1.0, 'song_metric_1': 20.0},
        ]
        climate_data = [
            {'lat': 0.0, 'lon': 0.0, 'temp': 25.0, 'precip': 100.0},
            {'lat': 10.0, 'lon': 10.0, 'temp': 15.0, 'precip': 50.0}, # Far away
        ]

        with open(self.raw_song_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=song_data[0].keys())
            writer.writeheader()
            writer.writerows(song_data)

        with open(self.raw_climate_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=climate_data[0].keys())
            writer.writeheader()
            writer.writerows(climate_data)
        
        initialize_checksums_file(self.checksum_path)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_haversine_distance(self):
        # Distance between (0,0) and (0,0) should be 0
        self.assertAlmostEqual(haversine_distance(0, 0, 0, 0), 0.0)
        # Distance between (0,0) and (1,0) approx 111km
        dist = haversine_distance(0, 0, 1, 0)
        self.assertGreater(dist, 100)
        self.assertLess(dist, 120)

    def test_perform_spatial_join(self):
        song_data = [
            {'species_id': 'sp1', 'lat': 0.0, 'lon': 0.0},
            {'species_id': 'sp2', 'lat': 1.0, 'lon': 1.0},
        ]
        climate_data = [
            {'lat': 0.0, 'lon': 0.0, 'temp': 25.0},
            {'lat': 1.0, 'lon': 1.0, 'temp': 20.0},
        ]
        
        joined = perform_spatial_join(song_data, climate_data, max_radius_km=100.0)
        
        self.assertEqual(len(joined), 2)
        # Check if climate data was merged
        self.assertIn('temp', joined[0])
        self.assertEqual(joined[0]['temp'], 25.0)

    def test_save_processed_data(self):
        data = [
            {'species_id': 'sp1', 'lat': 0.0, 'temp': 25.0, 'distance_km': 0.0},
            {'species_id': 'sp2', 'lat': 1.0, 'temp': 20.0, 'distance_km': 0.5},
        ]
        
        import logging
        logger = logging.getLogger("test")
        
        save_processed_data(data, self.output_path, logger)
        
        self.assertTrue(self.output_path.exists())
        
        # Verify content
        with open(self.output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['species_id'], 'sp1')
        
        # Verify checksum update
        self.assertTrue(self.checksum_path.exists())
        with open(self.checksum_path, 'r') as f:
            content = f.read()
        
        # Calculate expected checksum
        sha256_hash = hashlib.sha256()
        with open(self.output_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        expected_checksum = sha256_hash.hexdigest()
        
        self.assertIn(expected_checksum, content)
        self.assertIn(self.output_path.name, content)

    @patch('ingestion.load_config')
    @patch('ingestion.setup_ingestion_logger')
    @patch('ingestion.load_csv_with_validation')
    @patch('ingestion.process_song_records')
    @patch('ingestion.process_climate_snapshots')
    @patch('ingestion.perform_spatial_join')
    @patch('ingestion.save_processed_data')
    def test_main_execution_flow(
        self, mock_save, mock_join, mock_proc_clim, mock_proc_song, mock_load_csv, mock_logger, mock_config
    ):
        mock_config.return_value.get = lambda key, default=None: {
            'raw_song_path': self.raw_song_path,
            'raw_climate_path': self.raw_climate_path,
            'processed_dataset_path': self.output_path
        }.get(key, default)
        
        mock_logger.return_value = logging.getLogger("test")
        mock_load_csv.return_value = [{'lat': 0, 'lon': 0}]
        mock_proc_song.return_value = [{'lat': 0, 'lon': 0}]
        mock_proc_clim.return_value = [{'lat': 0, 'lon': 0}]
        mock_join.return_value = [{'lat': 0, 'lon': 0, 'temp': 20}]
        
        main()
        
        mock_save.assert_called_once()
        self.assertTrue(self.output_path.exists())

if __name__ == '__main__':
    unittest.main()