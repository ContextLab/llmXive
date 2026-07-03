"""
Contract test for the data/provenance.yaml schema.
Ensures that the provenance file adheres to the expected structure.
"""
import os
import yaml
import pytest
from pathlib import Path

# Import the module under test
from src.data.provenance import initialize_provenance_file, PROVENANCE_FILE_PATH


@pytest.fixture
def provenance_path():
    """Ensure the provenance file is initialized before testing."""
    initialize_provenance_file()
    return Path(PROVENANCE_FILE_PATH)


def test_provenance_file_exists(provenance_path):
    """Test that the provenance file is created."""
    assert provenance_path.exists(), "Provenance file should exist after initialization."


def test_provenance_schema_structure(provenance_path):
    """Test that the provenance file has the correct top-level keys."""
    with open(provenance_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict), "Provenance data should be a dictionary."
    assert "version" in data, "Missing 'version' key."
    assert "created_at" in data, "Missing 'created_at' key."
    assert "entries" in data, "Missing 'entries' key."
    assert isinstance(data["entries"], list), "'entries' should be a list."


def test_provenance_version_format(provenance_path):
    """Test that the version string is valid."""
    with open(provenance_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    version = data["version"]
    assert isinstance(version, str), "Version should be a string."
    # Simple check for semantic versioning format (e.g., 1.0.0)
    parts = version.split(".")
    assert len(parts) == 3, "Version should be in format X.Y.Z"


def test_provenance_entry_structure(provenance_path):
    """Test that entries follow the expected schema if added."""
    # Initialize empty first
    initialize_provenance_file()
    
    # Manually add a mock entry to test structure validation
    with open(provenance_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    mock_entry = {
        "timestamp": "2023-10-27T10:00:00",
        "source_type": "TEST",
        "source_url": "https://example.com",
        "output_path": "data/test.csv",
        "checksum": "abc123",
        "processing_params": {"key": "value"},
        "metadata": {}
    }
    data["entries"].append(mock_entry)
    
    with open(provenance_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

    # Reload and verify
    with open(provenance_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    entry = data["entries"][0]
    required_keys = [
        "timestamp", "source_type", "source_url", 
        "output_path", "checksum", "processing_params", "metadata"
    ]
    
    for key in required_keys:
        assert key in entry, f"Entry missing required key: {key}"
