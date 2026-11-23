import os
import sys
import unittest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validate_moderator_plot import (
    validate_plot_exists,
    validate_plot_content,
    validate_species_grouping,
    load_processed_data,
    load_moderator_results
)

class TestValidateModeratorPlot(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_data_path = Path(self.temp_dir) / "data" / "processed"
        self.mock_data_path.mkdir(parents=True)
        self.mock_results_path = Path(self.temp_dir) / "results"
        self.mock_results_path.mkdir(parents=True)
        
        # Create mock data
        self.mock_data = pd.DataFrame({
            'species': ['A', 'B', 'C', 'D', 'E', 'F'],
            'telomere_length_kb': [1.0, 2.0, 1.5, 2.5, 1.2, 2.2],
            'lifespan': [5, 10, 7, 12, 6, 11],
            'migration_status': ['Resident', 'Migratory', 'Resident', 'Migratory', 'Resident', 'Migratory']
        })
        
        self.mock_data.to_csv(self.mock_data_path / "merged_data.csv", index=False)
        
        # Create mock results
        pd.DataFrame({
            'interaction_coeff': [0.5],
            'interaction_p_value': [0.01]
        }).to_csv(self.mock_results_path / "moderator_analysis.csv", index=False)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch('validate_moderator_plot.get_config')
    def test_load_processed_data(self, mock_get_config):
        mock_get_config.return_value = {
            'paths': {'merged_data': str(self.mock_data_path / "merged_data.csv")}
        }
        data = load_processed_data()
        self.assertEqual(len(data), 6)
        self.assertIn('migration_status', data.columns)

    @patch('validate_moderator_plot.get_config')
    def test_load_moderator_results(self, mock_get_config):
        mock_get_config.return_value = {
            'paths': {'moderator_results': str(self.mock_results_path / "moderator_analysis.csv")}
        }
        results = load_moderator_results()
        self.assertIn('interaction_coeff', results.columns)

    def test_validate_plot_exists_missing(self):
        self.assertFalse(validate_plot_exists("/nonexistent/path.png"))

    def test_validate_plot_exists_empty_file(self):
        path = Path(self.temp_dir) / "empty.png"
        path.touch()
        self.assertFalse(validate_plot_exists(str(path)))

    def test_validate_plot_exists_valid(self):
        # Create a minimal valid PNG (1x1 red pixel)
        # PNG header + IHDR + IDAT + IEND
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
            0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE, 0x00, 0x00, 0x00,
            0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
            0x00, 0x03, 0x01, 0x01, 0x00, 0x18, 0xDD, 0x8D, 0xB4, 0x00, 0x00, 0x00,
            0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        path = Path(self.temp_dir) / "valid.png"
        path.write_bytes(png_data)
        self.assertTrue(validate_plot_exists(str(path)))

    def test_validate_plot_content_blank_image(self):
        # Create a blank white image (all 255)
        path = Path(self.temp_dir) / "blank.png"
        # Minimal valid PNG that is 1x1 white
        png_data = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
            0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE, 0x00, 0x00, 0x00,
            0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0xFF,
            0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00,
            0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82
        ])
        path.write_bytes(png_data)
        # This might pass the variance check depending on exact bytes, 
        # but for a 1x1 image, variance is 0.
        ok, errors = validate_plot_content(str(path), self.mock_data)
        # 1x1 image has 0 variance, so it should fail
        self.assertFalse(ok)
        self.assertTrue(any("low variance" in e for e in errors))

    def test_validate_species_grouping_missing_column(self):
        bad_data = self.mock_data.drop(columns=['migration_status'])
        ok, errors = validate_species_grouping(bad_data, "fake.png")
        self.assertFalse(ok)
        self.assertTrue(any("missing 'migration_status'" in e for e in errors))

    def test_validate_species_grouping_missing_groups(self):
        bad_data = self.mock_data.copy()
        bad_data['migration_status'] = 'Unknown'
        ok, errors = validate_species_grouping(bad_data, "fake.png")
        self.assertFalse(ok)
        self.assertTrue(any("missing required migration groups" in e for e in errors))

    def test_validate_species_grouping_success(self):
        ok, errors = validate_species_grouping(self.mock_data, "fake.png")
        self.assertTrue(ok)
        self.assertEqual(len(errors), 0)

if __name__ == '__main__':
    unittest.main()