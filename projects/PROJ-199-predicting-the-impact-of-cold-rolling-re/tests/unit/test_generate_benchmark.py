"""
Unit tests for the benchmark dataset generation (T018c).

These tests verify that:
1. The benchmark data is generated with the correct structure.
2. All required fields are present.
3. The data contains the expected materials and reduction levels.
"""
import pytest
import json
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.generate_benchmark import (
    generate_benchmark_data,
    validate_benchmark_data,
    main
)


class TestBenchmarkGeneration:
    """Tests for benchmark data generation."""

    def test_generate_data_structure(self):
        """Test that generated data has the correct top-level structure."""
        data = generate_benchmark_data()

        assert "metadata" in data, "Missing 'metadata' field"
        assert "data" in data, "Missing 'data' field"
        assert isinstance(data["data"], list), "'data' should be a list"

    def test_metadata_fields(self):
        """Test that metadata contains required fields."""
        data = generate_benchmark_data()

        required_metadata = ["source", "description", "materials", "reduction_levels"]
        for field in required_metadata:
            assert field in data["metadata"], f"Missing metadata field: {field}"

    def test_data_fields(self):
        """Test that each data entry contains required fields."""
        data = generate_benchmark_data()

        required_fields = ["material", "reduction", "brass", "copper", "s", "goss"]

        for entry in data["data"]:
            for field in required_fields:
                assert field in entry, f"Missing field '{field}' in entry: {entry}"

    def test_materials_present(self):
        """Test that Al, Cu, and Ni are all present."""
        data = generate_benchmark_data()
        materials = {entry["material"] for entry in data["data"]}

        expected_materials = {"Al", "Cu", "Ni"}
        assert materials == expected_materials, f"Expected {expected_materials}, got {materials}"

    def test_reduction_levels_present(self):
        """Test that all reduction levels are present for each material."""
        data = generate_benchmark_data()
        expected_levels = {0, 20, 40, 60, 80}

        for material in ["Al", "Cu", "Ni"]:
            material_levels = {
                entry["reduction"]
                for entry in data["data"]
                if entry["material"] == material
            }
            assert material_levels == expected_levels, (
                f"Material {material} missing levels: {expected_levels - material_levels}"
            )

    def test_value_ranges(self):
        """Test that volume fractions are within valid ranges [0, 1]."""
        data = generate_benchmark_data()

        for entry in data["data"]:
            for component in ["brass", "copper", "s", "goss"]:
                value = entry[component]
                assert 0 <= value <= 1, (
                    f"Value for {component} in {entry['material']} at {entry['reduction']}% "
                    f"reduction is out of range: {value}"
                )

    def test_validation_passes(self):
        """Test that the validation function passes on generated data."""
        data = generate_benchmark_data()
        assert validate_benchmark_data(data), "Validation failed on generated data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])