"""
Unit tests for the data_loader module.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from utils.data_loader import load_nist_references, DataValidationError, DiffusionReference


class TestDataLoader:
    """Tests for the data loader functionality."""

    def test_load_valid_json(self, tmp_path):
        """Test loading a valid JSON file."""
        # Create a temporary JSON file
        valid_data = {
            "metadata": {"version": "1.0"},
            "references": [
                {"solvent": "water", "temperature": 298.15, "value": 2.30e-9},
                {"solvent": "ethanol", "temperature": 298.15, "value": 1.10e-9}
            ]
        }
        json_file = tmp_path / "nist_refs.json"
        with open(json_file, 'w') as f:
            json.dump(valid_data, f)

        # Mock the NIST_REFS_PATH temporarily
        import utils.data_loader as dl
        original_path = dl.NIST_REFS_PATH
        dl.NIST_REFS_PATH = json_file

        try:
            refs = dl.load_nist_references()
            assert len(refs) == 2
            assert refs[0].solvent == "water"
            assert abs(refs[0].value - 2.30e-9) < 1e-15
        finally:
            dl.NIST_REFS_PATH = original_path

    def test_missing_file(self, tmp_path):
        """Test that FileNotFoundError is raised if file is missing."""
        import utils.data_loader as dl
        original_path = dl.NIST_REFS_PATH
        dl.NIST_REFS_PATH = tmp_path / "nonexistent.json"

        try:
            with pytest.raises(FileNotFoundError):
                dl.load_nist_references()
        finally:
            dl.NIST_REFS_PATH = original_path

    def test_invalid_json_format(self, tmp_path):
        """Test that DataValidationError is raised for invalid JSON structure."""
        # Create a JSON file that is not a list of references
        invalid_data = {"not_a_list": True}
        json_file = tmp_path / "nist_refs.json"
        with open(json_file, 'w') as f:
            json.dump(invalid_data, f)

        import utils.data_loader as dl
        original_path = dl.NIST_REFS_PATH
        dl.NIST_REFS_PATH = json_file

        try:
            with pytest.raises(DataValidationError):
                dl.load_nist_references()
        finally:
            dl.NIST_REFS_PATH = original_path

    def test_missing_required_fields(self, tmp_path):
        """Test that DataValidationError is raised for missing keys."""
        invalid_data = {
            "references": [
                {"solvent": "water"}  # Missing temperature and value
            ]
        }
        json_file = tmp_path / "nist_refs.json"
        with open(json_file, 'w') as f:
            json.dump(invalid_data, f)

        import utils.data_loader as dl
        original_path = dl.NIST_REFS_PATH
        dl.NIST_REFS_PATH = json_file

        try:
            with pytest.raises(DataValidationError):
                dl.load_nist_references()
        finally:
            dl.NIST_REFS_PATH = original_path

    def test_invalid_values(self, tmp_path):
        """Test that DataValidationError is raised for invalid values."""
        invalid_data = {
            "references": [
                {"solvent": "water", "temperature": -10, "value": 1.0}  # Negative temp
            ]
        }
        json_file = tmp_path / "nist_refs.json"
        with open(json_file, 'w') as f:
            json.dump(invalid_data, f)

        import utils.data_loader as dl
        original_path = dl.NIST_REFS_PATH
        dl.NIST_REFS_PATH = json_file

        try:
            with pytest.raises(DataValidationError):
                dl.load_nist_references()
        finally:
            dl.NIST_REFS_PATH = original_path
