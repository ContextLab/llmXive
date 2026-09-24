"""
Unit tests for data/join_guild_labels.py (T039c)
"""
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.join_guild_labels import (
    load_filtered_ebd,
    load_guild_mapping,
    validate_inputs,
    join_guild_labels,
    REQUIRED_BUFFERED_COLUMNS,
    REQUIRED_GUILD_COLUMNS
)
from utils.config import get_processed_dir


class TestJoinGuildLabels(unittest.TestCase):
    """Test cases for the join_guild_labels module."""

    def setUp(self):
        """Set up a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.processed_dir = Path(self.temp_dir)
        
        # Mock the config functions to use our temp directory
        import data.join_guild_labels as module
        module.PROCESSED_DIR = self.processed_dir
        module.INPUT_FILE = self.processed_dir / "buffered_observations.csv"
        module.GUILD_MAPPING_FILE = self.processed_dir / "guild_mapping.csv"
        module.OUTPUT_FILE = self.processed_dir / "joined_observations.csv"
        module.LOG_FILE = self.processed_dir / "guild_join_log.txt"

    def tearDown(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)

    def test_load_filtered_ebd_missing_file(self):
        """Test that loading a missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_filtered_ebd()

    def test_load_guild_mapping_missing_file(self):
        """Test that loading a missing guild mapping raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_guild_mapping()

    def test_validate_inputs_missing_columns_buffered(self):
        """Test validation fails when buffered data is missing columns."""
        # Create a DataFrame with missing columns
        df = pd.DataFrame({
            "species_id": ["A", "B"],
            "latitude": [1.0, 2.0],
            # Missing longitude and land cover columns
        })
        
        guild_df = pd.DataFrame({
            "species_id": ["A", "B"],
            "foraging_guild": ["g1", "g2"],
            "source_citation": ["src1", "src2"],
            "extraction_date": ["2024-01-01", "2024-01-01"]
        })
        
        with self.assertRaises(ValueError) as context:
            validate_inputs(df, guild_df)
        
        self.assertIn("Missing required columns", str(context.exception))

    def test_validate_inputs_missing_columns_guild(self):
        """Test validation fails when guild mapping is missing columns."""
        buffered_df = pd.DataFrame({
            "species_id": ["A"],
            "latitude": [1.0],
            "longitude": [1.0],
            "forest_prop_100m": [0.5],
            "grassland_prop_100m": [0.2],
            "wetland_prop_100m": [0.1],
            "urban_prop_100m": [0.1],
            "other_prop_100m": [0.1]
        })
        
        # Guild mapping missing extraction_date
        guild_df = pd.DataFrame({
            "species_id": ["A"],
            "foraging_guild": ["g1"],
            "source_citation": ["src1"],
            # Missing extraction_date
        })
        
        with self.assertRaises(ValueError) as context:
            validate_inputs(buffered_df, guild_df)
        
        self.assertIn("Missing required columns", str(context.exception))

    def test_validate_inputs_duplicate_species(self):
        """Test validation fails when guild mapping has duplicate species."""
        buffered_df = pd.DataFrame({
            "species_id": ["A"],
            "latitude": [1.0],
            "longitude": [1.0],
            "forest_prop_100m": [0.5],
            "grassland_prop_100m": [0.2],
            "wetland_prop_100m": [0.1],
            "urban_prop_100m": [0.1],
            "other_prop_100m": [0.1]
        })
        
        # Guild mapping with duplicate species_id
        guild_df = pd.DataFrame({
            "species_id": ["A", "A"],
            "foraging_guild": ["g1", "g2"],
            "source_citation": ["src1", "src2"],
            "extraction_date": ["2024-01-01", "2024-01-01"]
        })
        
        with self.assertRaises(ValueError) as context:
            validate_inputs(buffered_df, guild_df)
        
        self.assertIn("Duplicate species_id", str(context.exception))

    def test_join_guild_labels_success(self):
        """Test successful join when all species have guilds."""
        # Create buffered data
        buffered_df = pd.DataFrame({
            "species_id": ["A", "A", "B"],
            "latitude": [1.0, 2.0, 3.0],
            "longitude": [1.0, 2.0, 3.0],
            "forest_prop_100m": [0.5, 0.6, 0.4],
            "grassland_prop_100m": [0.2, 0.1, 0.3],
            "wetland_prop_100m": [0.1, 0.2, 0.2],
            "urban_prop_100m": [0.1, 0.1, 0.1],
            "other_prop_100m": [0.1, 0.0, 0.0]
        })
        
        # Save to file
        buffered_df.to_csv(self.processed_dir / "buffered_observations.csv", index=False)
        
        # Create guild mapping
        guild_df = pd.DataFrame({
            "species_id": ["A", "B"],
            "foraging_guild": ["canopy", "ground"],
            "source_citation": ["src1", "src2"],
            "extraction_date": ["2024-01-01", "2024-01-01"]
        })
        guild_df.to_csv(self.processed_dir / "guild_mapping.csv", index=False)
        
        # Load and validate
        loaded_buffered = load_filtered_ebd()
        loaded_guild = load_guild_mapping()
        validate_inputs(loaded_buffered, loaded_guild)
        
        # Perform join
        joined = join_guild_labels(loaded_buffered, loaded_guild)
        
        # Assertions
        self.assertEqual(len(joined), 3)
        self.assertTrue("foraging_guild" in joined.columns)
        self.assertFalse(joined["foraging_guild"].isna().any())
        
        # Check guild assignments
        self.assertEqual(joined.loc[joined["species_id"] == "A", "foraging_guild"].iloc[0], "canopy")
        self.assertEqual(joined.loc[joined["species_id"] == "B", "foraging_guild"].iloc[0], "ground")

    def test_join_guild_labels_missing_species(self):
        """Test that species without guilds are dropped and logged."""
        # Create buffered data with a species not in guild mapping
        buffered_df = pd.DataFrame({
            "species_id": ["A", "A", "B", "C"],  # C is missing from guild
            "latitude": [1.0, 2.0, 3.0, 4.0],
            "longitude": [1.0, 2.0, 3.0, 4.0],
            "forest_prop_100m": [0.5, 0.6, 0.4, 0.5],
            "grassland_prop_100m": [0.2, 0.1, 0.3, 0.2],
            "wetland_prop_100m": [0.1, 0.2, 0.2, 0.1],
            "urban_prop_100m": [0.1, 0.1, 0.1, 0.1],
            "other_prop_100m": [0.1, 0.0, 0.0, 0.1]
        })
        buffered_df.to_csv(self.processed_dir / "buffered_observations.csv", index=False)
        
        # Guild mapping missing species C
        guild_df = pd.DataFrame({
            "species_id": ["A", "B"],
            "foraging_guild": ["canopy", "ground"],
            "source_citation": ["src1", "src2"],
            "extraction_date": ["2024-01-01", "2024-01-01"]
        })
        guild_df.to_csv(self.processed_dir / "guild_mapping.csv", index=False)
        
        # Load and join
        loaded_buffered = load_filtered_ebd()
        loaded_guild = load_guild_mapping()
        joined = join_guild_labels(loaded_buffered, loaded_guild)
        
        # Assertions
        self.assertEqual(len(joined), 3)  # C should be dropped
        self.assertNotIn("C", joined["species_id"].values)
        
        # Check log file exists
        self.assertTrue(self.processed_dir / "guild_join_log.txt").exists()

    def test_join_preserves_all_columns(self):
        """Test that all buffered columns are preserved after join."""
        buffered_df = pd.DataFrame({
            "species_id": ["A"],
            "latitude": [1.0],
            "longitude": [1.0],
            "forest_prop_100m": [0.5],
            "grassland_prop_100m": [0.2],
            "wetland_prop_100m": [0.1],
            "urban_prop_100m": [0.1],
            "other_prop_100m": [0.1]
        })
        buffered_df.to_csv(self.processed_dir / "buffered_observations.csv", index=False)
        
        guild_df = pd.DataFrame({
            "species_id": ["A"],
            "foraging_guild": ["canopy"],
            "source_citation": ["src1"],
            "extraction_date": ["2024-01-01"]
        })
        guild_df.to_csv(self.processed_dir / "guild_mapping.csv", index=False)
        
        loaded_buffered = load_filtered_ebd()
        loaded_guild = load_guild_mapping()
        joined = join_guild_labels(loaded_buffered, loaded_guild)
        
        # All original buffered columns should be present
        for col in REQUIRED_BUFFERED_COLUMNS:
            self.assertIn(col, joined.columns)
        
        # Guild columns should be added
        self.assertIn("foraging_guild", joined.columns)
        self.assertIn("source_citation", joined.columns)
        self.assertIn("extraction_date", joined.columns)


if __name__ == "__main__":
    unittest.main()