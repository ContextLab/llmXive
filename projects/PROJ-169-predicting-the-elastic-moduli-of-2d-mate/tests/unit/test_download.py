"""
Unit tests for the unified dataset loader.
"""
import os
import json
import tempfile
from pathlib import Path
import pytest

from ingest.download import UnifiedDatasetLoader, DownloadManifest
from ingest.validator import enforce_single_source, clear_source_state

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)

@pytest.fixture
def clean_state():
    """Ensure no source state file exists before test."""
    clear_source_state()
    yield
    clear_source_state()

def test_loader_initialization(clean_state):
    """Test that loader initializes correctly."""
    loader = UnifiedDatasetLoader(source="materials_project")
    assert loader.source == "materials_project"
    assert loader.validate_source() is True

def test_loader_invalid_source(clean_state):
    """Test that loader rejects invalid source."""
    with pytest.raises(ValueError, match="Unsupported source"):
        UnifiedDatasetLoader(source="invalid_source")

def test_source_enforcement(clean_state):
    """Test that source enforcement works."""
    # First call should succeed
    enforce_single_source("materials_project")
    
    # Second call with same source should succeed
    enforce_single_source("materials_project")
    
    # Call with different source should fail
    with pytest.raises(SystemExit):
        enforce_single_source("aflow")

def test_fetch_data_creates_manifest(clean_state, temp_dir):
    """Test that fetch_data creates a manifest file."""
    loader = UnifiedDatasetLoader(source="materials_project")
    manifest = loader.fetch_data(temp_dir)
    
    assert isinstance(manifest, DownloadManifest)
    assert manifest.source == "materials_project"
    assert manifest.checksums is not None
    
    manifest_path = temp_dir / "download_manifest.json"
    assert manifest_path.exists()
    
    with open(manifest_path, "r") as f:
        data = json.load(f)
    
    assert "source" in data
    assert data["source"] == "materials_project"

def test_warning_in_metadata(clean_state):
    """Test that warning is present in metadata."""
    loader = UnifiedDatasetLoader(source="materials_project")
    metadata = loader.get_metadata()
    
    assert "warning" in metadata
    assert "surrogate interpolator" in metadata["warning"].lower()
    assert "schrödinger" not in metadata["warning"].lower() # Check for correct phrasing
