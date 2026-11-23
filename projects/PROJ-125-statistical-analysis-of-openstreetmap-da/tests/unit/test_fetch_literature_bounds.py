"""
Unit tests for fetch_literature_bounds module.
"""
import json
import tempfile
from pathlib import Path
import pytest

from code.fetch_literature_bounds import fetch_literature_bounds, save_bounds_to_json

class TestFetchLiteratureBounds:
    """Tests for the fetch_literature_bounds function."""

    def test_fetch_returns_dict(self):
        """Test that fetch_literature_bounds returns a dictionary."""
        result = fetch_literature_bounds()
        assert isinstance(result, dict)

    def test_fetch_has_required_keys(self):
        """Test that the fetched data contains required keys."""
        result = fetch_literature_bounds()
        assert "source" in result
        assert "bounds" in result
        assert "osm_only_max_r2" in result["bounds"]
        assert "osm_only_min_r2" in result["bounds"]

    def test_fetch_bounds_are_valid_floats(self):
        """Test that bound values are valid floats between 0 and 1."""
        result = fetch_literature_bounds()
        bounds = result["bounds"]

        for key, value in bounds.items():
            assert isinstance(value, (int, float)), f"Value for {key} is not numeric"
            assert 0.0 <= value <= 1.0, f"Value for {key} is out of range [0, 1]"

    def test_osm_only_max_greater_than_min(self):
        """Test that max bounds are greater than or equal to min bounds."""
        result = fetch_literature_bounds()
        bounds = result["bounds"]

        assert bounds["osm_only_max_r2"] >= bounds["osm_only_min_r2"]
        assert bounds["osm_with_height_max_r2"] >= bounds["osm_with_height_min_r2"]
        assert bounds["osm_with_socio_max_r2"] >= bounds["osm_with_socio_min_r2"]

class TestSaveBoundsToJson:
    """Tests for the save_bounds_to_json function."""

    def test_save_creates_file(self):
        """Test that save_bounds_to_json creates the output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_bounds.json"
            data = {"test": "data"}

            save_bounds_to_json(data, output_path)

            assert output_path.exists()

    def test_save_content_is_valid_json(self):
        """Test that the saved file contains valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_bounds.json"
            data = {"key": "value", "number": 42}

            save_bounds_to_json(data, output_path)

            with open(output_path, 'r') as f:
                loaded_data = json.load(f)

            assert loaded_data == data

    def test_save_creates_parent_directories(self):
        """Test that save_bounds_to_json creates parent directories if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "nested" / "test_bounds.json"
            data = {"test": "data"}

            save_bounds_to_json(data, output_path)

            assert output_path.exists()