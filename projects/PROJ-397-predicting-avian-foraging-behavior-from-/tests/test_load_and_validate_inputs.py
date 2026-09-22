"""
Tests for data/load_and_validate_inputs.py
"""
import os
import sys
import unittest
import tempfile
import shutil
import zipfile
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.load_and_validate_inputs import (
    load_filtered_ebd,
    load_guild_mapping,
    validate_nlcd_archive,
    validate_inputs,
    REQUIRED_EBD_COLUMNS,
    REQUIRED_GUILD_COLUMNS
)
from utils.config import get_processed_dir, get_raw_data_dir

class TestLoadAndValidateInputs(unittest.TestCase):
    
    def setUp(self):
        """Create a temporary directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.processed_dir = Path(self.temp_dir) / "processed"
        self.raw_dir = Path(self.temp_dir) / "raw"
        self.processed_dir.mkdir()
        self.raw_dir.mkdir()
        
        # Mock config functions to point to temp dirs
        self.patch_processed = patch('data.load_and_validate_inputs.get_processed_dir', return_value=self.processed_dir)
        self.patch_raw = patch('data.load_and_validate_inputs.get_raw_data_dir', return_value=self.raw_dir)
        self.mock_processed = self.patch_processed.start()
        self.mock_raw = self.patch_raw.start()

    def tearDown(self):
        """Clean up temporary directory."""
        self.patch_processed.stop()
        self.patch_raw.stop()
        shutil.rmtree(self.temp_dir)

    def test_load_filtered_ebd_success(self):
        """Test successful loading of valid filtered_ebd.csv."""
        df = pd.DataFrame({
            'species_id': ['sp1', 'sp2', 'sp3'],
            'latitude': [40.0, -30.0, 0.0],
            'longitude': [-70.0, 60.0, 10.0],
            'extra_col': [1, 2, 3]
        })
        df.to_csv(self.processed_dir / "filtered_ebd.csv", index=False)
        
        loaded = load_filtered_ebd()
        self.assertEqual(len(loaded), 3)
        self.assertTrue(set(REQUIRED_EBD_COLUMNS).issubset(set(loaded.columns)))

    def test_load_filtered_ebd_missing_file(self):
        """Test that FileNotFoundError is raised if file is missing."""
        with self.assertRaises(FileNotFoundError):
            load_filtered_ebd()

    def test_load_filtered_ebd_missing_columns(self):
        """Test that ValueError is raised if required columns are missing."""
        df = pd.DataFrame({
            'species_id': ['sp1'],
            'wrong_lat': [40.0]
        })
        df.to_csv(self.processed_dir / "filtered_ebd.csv", index=False)
        
        with self.assertRaises(ValueError):
            load_filtered_ebd()

    def test_load_filtered_ebd_invalid_coords(self):
        """Test that ValueError is raised for out-of-range coordinates."""
        df = pd.DataFrame({
            'species_id': ['sp1'],
            'latitude': [100.0],  # Invalid
            'longitude': [40.0]
        })
        df.to_csv(self.processed_dir / "filtered_ebd.csv", index=False)
        
        with self.assertRaises(ValueError):
            load_filtered_ebd()

    def test_load_guild_mapping_success(self):
        """Test successful loading of valid guild_mapping.csv."""
        df = pd.DataFrame({
            'species_id': ['sp1', 'sp2'],
            'foraging_guild': ['granivore', 'insectivore']
        })
        df.to_csv(self.processed_dir / "guild_mapping.csv", index=False)
        
        loaded = load_guild_mapping()
        self.assertEqual(len(loaded), 2)
        self.assertTrue(set(REQUIRED_GUILD_COLUMNS).issubset(set(loaded.columns)))

    def test_load_guild_mapping_missing_file(self):
        """Test that FileNotFoundError is raised if file is missing."""
        with self.assertRaises(FileNotFoundError):
            load_guild_mapping()

    def test_load_guild_mapping_missing_columns(self):
        """Test that ValueError is raised if required columns are missing."""
        df = pd.DataFrame({
            'species_id': ['sp1'],
            'guild': ['granivore']  # Wrong column name
        })
        df.to_csv(self.processed_dir / "guild_mapping.csv", index=False)
        
        with self.assertRaises(ValueError):
            load_guild_mapping()

    def test_validate_nlcd_archive_success(self):
        """Test successful validation of a valid NLCD zip."""
        zip_path = self.raw_dir / "nlcd_2019.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("NLCD_2019.tif", "fake raster data")
        
        path, zf_obj = validate_nlcd_archive()
        self.assertEqual(path, zip_path)
        self.assertIsInstance(zf_obj, zipfile.ZipFile)
        zf_obj.close()

    def test_validate_nlcd_archive_missing_file(self):
        """Test that FileNotFoundError is raised if archive is missing."""
        with self.assertRaises(FileNotFoundError):
            validate_nlcd_archive()

    def test_validate_nlcd_archive_empty(self):
        """Test that ValueError is raised for empty archive."""
        zip_path = self.raw_dir / "nlcd_2019.zip"
        with zipfile.ZipFile(zip_path, 'w'):
            pass  # Empty zip
        
        with self.assertRaises(ValueError):
            validate_nlcd_archive()

    def test_validate_nlcd_archive_no_raster(self):
        """Test that ValueError is raised if no raster files found."""
        zip_path = self.raw_dir / "nlcd_2019.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("readme.txt", "no raster here")
        
        with self.assertRaises(ValueError):
            validate_nlcd_archive()

    def test_validate_inputs_success(self):
        """Test successful cross-validation."""
        ebd_df = pd.DataFrame({
            'species_id': ['sp1', 'sp2', 'sp3'],
            'latitude': [40.0, -30.0, 0.0],
            'longitude': [-70.0, 60.0, 10.0]
        })
        guild_df = pd.DataFrame({
            'species_id': ['sp2', 'sp3', 'sp4'],
            'foraging_guild': ['insectivore', 'granivore', 'carnivore']
        })
        
        result = validate_inputs(ebd_df, guild_df, Path("fake.zip"))
        self.assertTrue(result)

    def test_validate_inputs_no_intersection(self):
        """Test that ValueError is raised if no common species."""
        ebd_df = pd.DataFrame({
            'species_id': ['sp1'],
            'latitude': [40.0],
            'longitude': [-70.0]
        })
        guild_df = pd.DataFrame({
            'species_id': ['sp2'],
            'foraging_guild': ['insectivore']
        })
        
        with self.assertRaises(ValueError):
            validate_inputs(ebd_df, guild_df, Path("fake.zip"))

if __name__ == '__main__':
    unittest.main()