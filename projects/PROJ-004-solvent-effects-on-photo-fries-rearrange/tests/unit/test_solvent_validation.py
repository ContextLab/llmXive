"""
Unit tests for solvent property validation in code/data/loaders.py.

This module validates that dielectric constants are correctly loaded and
match the versioned lookup table defined in data/chemicals/solvents.yaml.
"""

import os
import sys
import unittest
import yaml
from unittest.mock import patch, mock_open

# Add the project root to the path to allow imports from 'code'
# Assuming this test file is at tests/unit/test_solvent_validation.py
# and the project root is two levels up.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.loaders import (
    get_solvent_properties,
    get_all_solvents,
    get_dielectric_constant_range,
    SolventDataError,
    _load_solvent_manifest,
    _SOLVENTS_FILE_PATH
)
from utils.logging import setup_logging


class TestSolventValidation(unittest.TestCase):
    """Tests for solvent property loading and validation."""

    @classmethod
    def setUpClass(cls):
        """Set up logging for the test suite."""
        setup_logging(level="DEBUG")

    def _get_mock_manifest(self):
        """Helper to create a valid mock manifest structure."""
        return {
            "metadata": {
                "source": "NIST Standard Reference Database",
                "version": "1.0.0"
            },
            "solvents": [
                {
                    "name": "hexane",
                    "dielectric_constant": 1.88,
                    "source_id": "NIST-12345",
                    "notes": "Non-polar reference"
                },
                {
                    "name": "acetone",
                    "dielectric_constant": 20.7,
                    "source_id": "NIST-67890",
                    "notes": "Moderate polarity"
                },
                {
                    "name": "water",
                    "dielectric_constant": 78.4,
                    "source_id": "NIST-11111",
                    "notes": "High polarity"
                }
            ]
        }

    @patch('data.loaders.open', new_callable=mock_open, read_data="")
    @patch('data.loaders.os.path.exists', return_value=True)
    def test_load_solvent_manifest_missing_file(self, mock_exists, mock_file):
        """Test that SolventDataError is raised if the file does not exist."""
        mock_exists.return_value = False
        with self.assertRaises(SolventDataError) as context:
            _load_solvent_manifest()
        self.assertIn("not found", str(context.exception))

    @patch('data.loaders.yaml.safe_load')
    @patch('data.loaders.open', new_callable=mock_open, read_data="")
    @patch('data.loaders.os.path.exists', return_value=True)
    def test_load_solvent_manifest_empty_file(self, mock_exists, mock_file, mock_yaml):
        """Test that SolventDataError is raised if the file is empty."""
        mock_yaml.return_value = None
        with self.assertRaises(SolventDataError) as context:
            _load_solvent_manifest()
        self.assertIn("empty", str(context.exception))

    @patch('data.loaders.yaml.safe_load')
    @patch('data.loaders.open', new_callable=mock_open, read_data="")
    @patch('data.loaders.os.path.exists', return_value=True)
    def test_load_solvent_manifest_invalid_structure(self, mock_exists, mock_file, mock_yaml):
        """Test that SolventDataError is raised if 'solvents' key is missing."""
        mock_yaml.return_value = {"metadata": {}}
        with self.assertRaises(SolventDataError) as context:
            _load_solvent_manifest()
        self.assertIn("Invalid manifest structure", str(context.exception))

    @patch('data.loaders._load_solvent_manifest')
    def test_get_solvent_properties_success(self, mock_load):
        """Test successful retrieval of solvent properties."""
        mock_load.return_value = self._get_mock_manifest()
        
        result = get_solvent_properties("acetone")
        
        self.assertEqual(result["name"], "acetone")
        self.assertAlmostEqual(result["dielectric_constant"], 20.7, places=2)
        self.assertEqual(result["source_id"], "NIST-67890")
        self.assertIn("notes", result)

    @patch('data.loaders._load_solvent_manifest')
    def test_get_solvent_properties_not_found(self, mock_load):
        """Test that SolventDataError is raised for unknown solvent."""
        mock_load.return_value = self._get_mock_manifest()
        
        with self.assertRaises(SolventDataError) as context:
            get_solvent_properties("unknown_solvent")
        
        self.assertIn("not found", str(context.exception))
        self.assertIn("Available", str(context.exception))

    @patch('data.loaders._load_solvent_manifest')
    def test_get_solvent_properties_missing_field(self, mock_load):
        """Test that SolventDataError is raised if required fields are missing."""
        manifest = self._get_mock_manifest()
        # Corrupt an entry
        manifest["solvents"][0]["dielectric_constant"] = None
        manifest["solvents"][0].pop("source_id")
        mock_load.return_value = manifest
        
        with self.assertRaises(SolventDataError) as context:
            get_solvent_properties("hexane")
        
        self.assertIn("missing required field", str(context.exception))

    @patch('data.loaders._load_solvent_manifest')
    def test_get_all_solvents_valid_entries(self, mock_load):
        """Test that get_all_solvents returns only valid entries."""
        mock_load.return_value = self._get_mock_manifest()
        
        result = get_all_solvents()
        
        self.assertEqual(len(result), 3)
        for solvent in result:
            self.assertIn("name", solvent)
            self.assertIn("dielectric_constant", solvent)
            self.assertIn("source_id", solvent)

    @patch('data.loaders._load_solvent_manifest')
    def test_get_all_solvents_skips_invalid(self, mock_load):
        """Test that get_all_solvents skips entries with missing fields."""
        manifest = self._get_mock_manifest()
        # Add an invalid entry
        manifest["solvents"].append({"name": "bad_solvent"})
        mock_load.return_value = manifest
        
        result = get_all_solvents()
        
        # Should still have the 3 valid ones, the invalid one is skipped
        self.assertEqual(len(result), 3)
        names = [s["name"] for s in result]
        self.assertNotIn("bad_solvent", names)

    @patch('data.loaders.get_all_solvents')
    def test_get_dielectric_constant_range(self, mock_get_all):
        """Test calculation of dielectric constant range."""
        mock_get_all.return_value = [
            {"name": "low", "dielectric_constant": 2.0},
            {"name": "high", "dielectric_constant": 80.0},
            {"name": "mid", "dielectric_constant": 20.0}
        ]
        
        result = get_dielectric_constant_range()
        
        self.assertEqual(result["min"], 2.0)
        self.assertEqual(result["max"], 80.0)

    @patch('data.loaders.get_all_solvents')
    def test_get_dielectric_constant_range_empty(self, mock_get_all):
        """Test that SolventDataError is raised if no solvents found."""
        mock_get_all.return_value = []
        
        with self.assertRaises(SolventDataError) as context:
            get_dielectric_constant_range()
        
        self.assertIn("No valid solvents found", str(context.exception))


if __name__ == "__main__":
    unittest.main()