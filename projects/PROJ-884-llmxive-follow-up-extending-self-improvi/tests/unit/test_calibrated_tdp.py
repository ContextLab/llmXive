import unittest
import json
import os
from pathlib import Path
from code.utils.generate_tdp_constant import generate_calibrated_tdp, save_calibrated_tdp

class TestCalibratedTDP(unittest.TestCase):

    def test_tdp_constant_valid(self):
        # Create a dummy calibration data
        calibration_data = {
            "estimated_tdp_watts": 75.0,
            "source": "verified-literature",
            "citation_url": "https://example.com/tdp_source"
        }

        # Output file path
        output_file = "data/processed/calibrated_tdp.json"

        # Generate calibrated TDP data
        calibrated_tdp = generate_calibrated_tdp(calibration_data)

        # Save the data to the output file
        save_calibrated_tdp(calibrated_tdp, output_file)

        # Check if the file exists
        self.assertTrue(Path(output_file).exists())

        # Load the data from the file
        with open(output_file, 'r') as f:
            loaded_data = json.load(f)

        # Assert that the TDP value is greater than 0
        self.assertGreater(loaded_data['tdp_watts'], 0)

        # Assert that the source is present
        self.assertIn('source', loaded_data)

        # Assert that the citation URL is present and valid
        self.assertIn('citation_url', loaded_data)
        self.assertTrue(loaded_data['citation_url'])

        # Clean up the output file
        os.remove(output_file)
