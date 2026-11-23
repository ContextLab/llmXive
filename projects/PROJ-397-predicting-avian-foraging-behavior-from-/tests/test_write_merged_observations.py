import os
import sys
import unittest
import tempfile
import shutil
import csv
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from data.write_merged_observations import (
    load_joined_data,
    validate_schema,
    write_merged_observations,
    REQUIRED_COLUMNS
)

class TestWriteMergedObservations(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(self.temp_dir, "input.csv")
        self.output_file = os.path.join(self.temp_dir, "output.csv")
        
        # Create valid test data
        self.valid_data = [
            {
                "species_id": "A001",
                "foraging_guild": "ground",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "observation_date": "2023-05-01",
                "forest_prop_100m": 0.2,
                "grassland_prop_100m": 0.5,
                "wetland_prop_100m": 0.1,
                "urban_prop_100m": 0.1,
                "other_prop_100m": 0.1
            },
            {
                "species_id": "A002",
                "foraging_guild": "canopy",
                "latitude": 41.8781,
                "longitude": -87.6298,
                "observation_date": "2023-05-02",
                "forest_prop_100m": 0.8,
                "grassland_prop_100m": 0.05,
                "wetland_prop_100m": 0.05,
                "urban_prop_100m": 0.05,
                "other_prop_100m": 0.05
            }
        ]
        
        # Write input file
        with open(self.input_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
            for row in self.valid_data:
                writer.writerow(row)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_joined_data(self):
        """Test loading valid joined data."""
        data = load_joined_data(self.input_file)
        self.assertEqual(len(data), 2)
        self.assertIn("species_id", data[0])
        self.assertIn("foraging_guild", data[0])
        self.assertIsInstance(data[0]["latitude"], float)

    def test_validate_schema_valid(self):
        """Test schema validation with valid data."""
        data = load_joined_data(self.input_file)
        # Should not raise
        validate_schema(data)

    def test_validate_schema_missing_column(self):
        """Test schema validation fails with missing column."""
        data = load_joined_data(self.input_file)
        # Remove a required column
        del data[0]["forest_prop_100m"]
        with self.assertRaises(ValueError) as context:
            validate_schema(data)
        self.assertIn("Missing required columns", str(context.exception))

    def test_validate_schema_invalid_latitude(self):
        """Test schema validation fails with invalid latitude."""
        data = load_joined_data(self.input_file)
        data[0]["latitude"] = 100.0  # Invalid
        with self.assertRaises(ValueError) as context:
            validate_schema(data)
        self.assertIn("Invalid latitude", str(context.exception))

    def test_validate_schema_proportions_sum(self):
        """Test schema validation fails if proportions don't sum to 1."""
        data = load_joined_data(self.input_file)
        data[0]["forest_prop_100m"] = 0.9  # Sum will be > 1.0
        with self.assertRaises(ValueError) as context:
            validate_schema(data)
        self.assertIn("do not sum to ~1.0", str(context.exception))

    def test_write_merged_observations(self):
        """Test writing merged observations to file."""
        data = load_joined_data(self.input_file)
        write_merged_observations(data, self.output_file)
        
        self.assertTrue(os.path.exists(self.output_file))
        
        with open(self.output_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["species_id"], "A001")
        self.assertEqual(rows[0]["foraging_guild"], "ground")

    def test_write_merged_observations_creates_directory(self):
        """Test that write_merged_observations creates the output directory."""
        data = load_joined_data(self.input_file)
        nested_output = os.path.join(self.temp_dir, "nested", "dir", "output.csv")
        write_merged_observations(data, nested_output)
        self.assertTrue(os.path.exists(nested_output))

if __name__ == "__main__":
    unittest.main()