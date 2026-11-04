"""
Unit Tests for Registry Generator (T008)
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch
import sys
import os

# Ensure the src directory is in the path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.services.registry_generator import generate_registry, write_registry


class TestRegistryGenerator:
    """Test cases for the registry generator logic."""

    def test_generate_registry_valid_data(self):
        """Test registry generation with valid input data."""
        mock_verified_ids = {
            "N1000": ["zenodo_1000_a", "zenodo_1000_b"],
            "N2000": ["zenodo_2000_a"],
            "N4000": ["zenodo_4000_a", "zenodo_4000_b", "zenodo_4000_c"]
        }

        result = generate_registry(mock_verified_ids)

        assert "N1000" in result
        assert "N2000" in result
        assert "N4000" in result
        assert result["N1000"] == ["zenodo_1000_a", "zenodo_1000_b"]
        assert result["N2000"] == ["zenodo_2000_a"]
        assert result["N4000"] == ["zenodo_4000_a", "zenodo_4000_b", "zenodo_4000_c"]

    def test_generate_registry_missing_size(self):
        """Test registry generation when a size is missing from verified IDs."""
        mock_verified_ids = {
            "N1000": ["zenodo_1000_a"],
            # N2000 missing
            "N4000": ["zenodo_4000_a"]
        }

        result = generate_registry(mock_verified_ids)

        assert "N1000" in result
        assert "N2000" in result
        assert "N4000" in result
        assert result["N2000"] == []  # Should be empty list

    def test_generate_registry_empty_all(self):
        """Test that an error is raised if no IDs are found for any size."""
        mock_verified_ids = {
            "N1000": [],
            "N2000": [],
            "N4000": []
        }

        with pytest.raises(ValueError, match="Registry generation failed"):
            generate_registry(mock_verified_ids)

    def test_write_registry_creates_file(self, tmp_path):
        """Test that write_registry creates the JSON file correctly."""
        registry = {
            "N1000": ["id_1"],
            "N2000": ["id_2"]
        }
        output_path = tmp_path / "data" / "metadata" / "dataset_registry.json"

        write_registry(registry, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            loaded_data = json.load(f)
        assert loaded_data == registry

    def test_write_registry_creates_directories(self, tmp_path):
        """Test that write_registry creates parent directories if they don't exist."""
        registry = {"N1000": ["id_1"]}
        # Deep nested path that doesn't exist
        output_path = tmp_path / "deep" / "nested" / "path" / "registry.json"

        write_registry(registry, output_path)

        assert output_path.exists()