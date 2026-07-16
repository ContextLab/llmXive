"""
Tests for data directory structure setup.
Verifies that the required directories and files are created correctly.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to import the setup script logic
# Since the script is in code/, we add the parent to path
import sys
from unittest.mock import patch

# Import the main function from the setup script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))
from setup_data_structure import (
    ensure_directory, 
    initialize_checksums_file, 
    GRAPH_METADATA_SCHEMA, 
    SIMULATION_RESULT_SCHEMA
)


class TestDataStructureSetup:
    """Test cases for data structure setup functions."""

    def test_ensure_directory_creates_new_dir(self, tmp_path):
        """Test that ensure_directory creates a new directory."""
        new_dir = tmp_path / "new" / "nested" / "dir"
        assert not new_dir.exists()
        
        ensure_directory(new_dir)
        
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_exists_no_error(self, tmp_path):
        """Test that ensure_directory doesn't error on existing dir."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        
        # Should not raise
        ensure_directory(existing_dir)
        
        assert existing_dir.exists()

    def test_initialize_checksums_creates_file(self, tmp_path):
        """Test that initialize_checksums_file creates the file."""
        checksum_file = tmp_path / "checksums.txt"
        
        initialize_checksums_file(checksum_file)
        
        assert checksum_file.exists()
        content = checksum_file.read_text()
        assert "# Checksums for generated artifacts" in content

    def test_initialize_checksums_preserves_existing(self, tmp_path):
        """Test that initialize_checksums_file doesn't overwrite existing file."""
        checksum_file = tmp_path / "checksums.txt"
        original_content = "# Existing content\n"
        checksum_file.write_text(original_content)
        
        initialize_checksums_file(checksum_file)
        
        assert checksum_file.read_text() == original_content

    def test_schemas_are_valid_json(self):
        """Test that the schema definitions are valid JSON-serializable."""
        # This will raise if schemas are invalid
        json_str_graph = json.dumps(GRAPH_METADATA_SCHEMA)
        json_str_sim = json.dumps(SIMULATION_RESULT_SCHEMA)
        
        assert json_str_graph is not None
        assert json_str_sim is not None

    def test_schema_has_required_fields(self):
        """Test that schemas have required fields defined."""
        assert "graph_metadata" in {"graph_metadata": GRAPH_METADATA_SCHEMA}
        assert "required" in GRAPH_METADATA_SCHEMA
        assert "rewiring_probability" in GRAPH_METADATA_SCHEMA["required"]
        
        assert "required" in SIMULATION_RESULT_SCHEMA
        assert "critical_coupling" in SIMULATION_RESULT_SCHEMA["required"]