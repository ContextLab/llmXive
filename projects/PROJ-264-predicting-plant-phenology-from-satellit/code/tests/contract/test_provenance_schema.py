"""
Contract tests for the provenance.yaml schema.

These tests verify that the provenance file adheres to the expected
structure and data types as defined in the project specifications.
"""

import os
import yaml
import pytest
from pathlib import Path
from datetime import datetime

from src.data.provenance import initialize_provenance_file, PROVENANCE_FILE_PATH
from src.lib.utils import setup_logging

logger = setup_logging(__name__)

# Path to the provenance file
provenance_path = PROVENANCE_FILE_PATH


@pytest.fixture(scope="module", autouse=True)
def ensure_provenance_exists():
    """Ensure the provenance file exists before running tests."""
    if not provenance_path.exists():
        initialize_provenance_file()
    yield
    

def test_provenance_file_exists():
    """Test that the provenance file exists."""
    assert provenance_path.exists(), f"Provenance file not found at {provenance_path}"


def test_provenance_schema_structure():
    """Test that the provenance file has the required top-level keys."""
    with open(provenance_path, "r") as f:
        data = yaml.safe_load(f)
    
    required_keys = [
        "version",
        "project_id",
        "created_at",
        "last_updated",
        "processing_params",
        "data_sources",
        "processing_steps",
        "execution_log",
        "metadata"
    ]
    
    for key in required_keys:
        assert key in data, f"Missing required key in provenance: {key}"
    
    # Verify types
    assert isinstance(data["version"], str), "version must be a string"
    assert isinstance(data["project_id"], str), "project_id must be a string"
    assert isinstance(data["processing_params"], dict), "processing_params must be a dict"
    assert isinstance(data["data_sources"], list), "data_sources must be a list"
    assert isinstance(data["processing_steps"], list), "processing_steps must be a list"
    assert isinstance(data["execution_log"], list), "execution_log must be a list"
    assert isinstance(data["metadata"], dict), "metadata must be a dict"


def test_provenance_version_format():
    """Test that the version follows semantic versioning."""
    with open(provenance_path, "r") as f:
        data = yaml.safe_load(f)
    
    version = data["version"]
    # Basic semantic versioning check (X.Y.Z)
    parts = version.split(".")
    assert len(parts) == 3, f"Version should have 3 parts (X.Y.Z), got: {version}"
    assert all(p.isdigit() for p in parts), f"Version parts should be numeric: {version}"


def test_provenance_entry_structure():
    """Test that data_sources and processing_steps have the correct structure."""
    with open(provenance_path, "r") as f:
        data = yaml.safe_load(f)
    
    # Test data_sources structure (if any exist)
    if data["data_sources"]:
        for source in data["data_sources"]:
            assert "name" in source, "Data source missing 'name'"
            assert "type" in source, "Data source missing 'type'"
            assert "provider" in source, "Data source missing 'provider'"
            assert "endpoint" in source, "Data source missing 'endpoint'"
            assert "date_range" in source, "Data source missing 'date_range'"
            assert "checksums" in source, "Data source missing 'checksums'"
            assert "status" in source, "Data source missing 'status'"
            
            # Validate date_range structure
            date_range = source["date_range"]
            assert "start" in date_range, "date_range missing 'start'"
            assert "end" in date_range, "date_range missing 'end'"
    
    # Test processing_steps structure (if any exist)
    if data["processing_steps"]:
        for step in data["processing_steps"]:
            assert "id" in step, "Processing step missing 'id'"
            assert "name" in step, "Processing step missing 'name'"
            assert "description" in step, "Processing step missing 'description'"
            assert "script" in step, "Processing step missing 'script'"
            assert "parameters" in step, "Processing step missing 'parameters'"
            assert "outputs" in step, "Processing step missing 'outputs'"
            assert "checksums" in step, "Processing step missing 'checksums'"
            assert "status" in step, "Processing step missing 'status'"
            
            # Validate outputs is a list
            assert isinstance(step["outputs"], list), "outputs must be a list"

def test_processing_params_structure():
    """Test that processing_params has the required fields."""
    with open(provenance_path, "r") as f:
        data = yaml.safe_load(f)
    
    params = data["processing_params"]
    required_params = [
        "software_version",
        "python_version",
        "random_seed",
        "cloud_coverage_threshold",
        "spatial_resolution",
        "temporal_resolution"
    ]
    
    for param in required_params:
        assert param in params, f"Missing processing parameter: {param}"
    
    # Validate types
    assert isinstance(params["random_seed"], int), "random_seed must be an integer"
    assert isinstance(params["cloud_coverage_threshold"], (int, float)), "cloud_coverage_threshold must be numeric"
    assert 0 <= params["cloud_coverage_threshold"] <= 1, "cloud_coverage_threshold must be between 0 and 1"

def test_metadata_structure():
    """Test that metadata has the required fields."""
    with open(provenance_path, "r") as f:
        data = yaml.safe_load(f)
    
    metadata = data["metadata"]
    required_metadata = ["git_commit", "environment", "notes"]
    
    for key in required_metadata:
        assert key in metadata, f"Missing metadata field: {key}"
        assert isinstance(metadata[key], str), f"metadata.{key} must be a string"