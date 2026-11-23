"""
Unit tests for the registry generator (T055a).
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.registry_generator import generate_registry, write_registry
from src.lib.config import VERIFIED_DATASET_IDS


class TestRegistryGenerator:
    """Tests for the registry generation logic."""

    def test_generate_registry_with_valid_data(self):
        """Test generation with a valid list of dataset IDs."""
        mock_data = [
            {"id": "zenodo_1000_a", "size": 1000},
            {"id": "zenodo_1000_b", "size": 1000},
            {"id": "zenodo_2000_a", "size": 2000},
            {"id": "zenodo_4000_a", "size": 4000},
            {"id": "zenodo_500_a", "size": 500},  # Should be ignored
        ]

        with patch("src.services.registry_generator.VERIFIED_DATASET_IDS", mock_data):
            registry = generate_registry()

        assert 1000 in registry
        assert 2000 in registry
        assert 4000 in registry
        assert "zenodo_1000_a" in registry[1000]
        assert "zenodo_1000_b" in registry[1000]
        assert "zenodo_2000_a" in registry[2000]
        assert "zenodo_4000_a" in registry[4000]
        assert 500 not in registry

    def test_generate_registry_missing_sizes(self):
        """Test generation when some sizes are missing."""
        mock_data = [
            {"id": "zenodo_1000_a", "size": 1000},
            # 2000 and 4000 missing
        ]

        with patch("src.services.registry_generator.VERIFIED_DATASET_IDS", mock_data):
            registry = generate_registry()

        assert 1000 in registry
        assert 2000 not in registry
        assert 4000 not in registry

    def test_generate_registry_empty_input(self):
        """Test generation with empty input."""
        with patch("src.services.registry_generator.VERIFIED_DATASET_IDS", []):
            with pytest.raises(ValueError, match="No verified dataset IDs found"):
                generate_registry()

    def test_write_registry_creates_file(self, tmp_path):
        """Test that write_registry creates the output file."""
        registry = {1000: ["id1"], 2000: ["id2"]}
        output_path = tmp_path / "registry.json"

        write_registry(registry, output_path)

        assert output_path.exists()
        with open(output_path, "r") as f:
            data = json.load(f)
        assert data == registry

    def test_write_registry_creates_directories(self, tmp_path):
        """Test that write_registry creates parent directories if needed."""
        registry = {1000: ["id1"]}
        output_path = tmp_path / "subdir" / "registry.json"

        write_registry(registry, output_path)

        assert output_path.exists()
        assert output_path.parent.exists()