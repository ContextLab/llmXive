"""
Unit tests for SC-005 ratio calculator.
"""
import json
import tempfile
from pathlib import Path
import pytest

from sc005_ratio_calculator import (
    load_json_file,
    save_json_file,
    calculate_sc005_ratio,
)


class TestCalculateSC005Ratio:
    """Tests for the calculate_sc005_ratio function."""

    def test_calculate_ratio_normal_case(self):
        """Test normal calculation with valid inputs."""
        species_counts = {
            'total_species_input': 100,
            'excluded_species_count': 20
        }
        ratio = calculate_sc005_ratio(species_counts)
        assert ratio == 0.2
        assert isinstance(ratio, float)

    def test_calculate_ratio_zero_excluded(self):
        """Test when no species are excluded."""
        species_counts = {
            'total_species_input': 50,
            'excluded_species_count': 0
        }
        ratio = calculate_sc005_ratio(species_counts)
        assert ratio == 0.0

    def test_calculate_ratio_all_excluded(self):
        """Test when all species are excluded."""
        species_counts = {
            'total_species_input': 30,
            'excluded_species_count': 30
        }
        ratio = calculate_sc005_ratio(species_counts)
        assert ratio == 1.0

    def test_calculate_ratio_missing_keys(self):
        """Test that missing keys raise KeyError."""
        species_counts = {
            'total_species_input': 100
            # missing 'excluded_species_count'
        }
        with pytest.raises(KeyError):
            calculate_sc005_ratio(species_counts)

    def test_calculate_ratio_zero_division(self):
        """Test that zero total species raises ZeroDivisionError."""
        species_counts = {
            'total_species_input': 0,
            'excluded_species_count': 0
        }
        with pytest.raises(ZeroDivisionError):
            calculate_sc005_ratio(species_counts)

    def test_calculate_ratio_float_precision(self):
        """Test ratio calculation with non-integer result."""
        species_counts = {
            'total_species_input': 7,
            'excluded_species_count': 3
        }
        ratio = calculate_sc005_ratio(species_counts)
        expected = 3 / 7
        assert abs(ratio - expected) < 1e-10


class TestLoadAndSaveJson:
    """Tests for JSON file I/O functions."""

    def test_save_and_load_json(self, tmp_path):
        """Test saving and loading a JSON file."""
        test_data = {
            'key1': 'value1',
            'key2': 123,
            'key3': [1, 2, 3]
        }
        file_path = tmp_path / 'test.json'

        save_json_file(file_path, test_data)
        loaded_data = load_json_file(file_path)

        assert loaded_data == test_data

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a file that doesn't exist."""
        file_path = tmp_path / 'nonexistent.json'
        with pytest.raises(FileNotFoundError):
            load_json_file(file_path)

    def test_load_invalid_json(self, tmp_path):
        """Test loading a file with invalid JSON."""
        file_path = tmp_path / 'invalid.json'
        file_path.write_text('not valid json {')

        with pytest.raises(ValueError):
            load_json_file(file_path)