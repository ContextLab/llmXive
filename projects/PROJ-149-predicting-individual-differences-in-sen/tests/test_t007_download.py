"""
Tests for T007: Download Data.
"""
import os
import json
import pytest
from pathlib import Path
import sys

# Add code to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from config import get_path, ensure_dirs

def test_manifest_exists():
    """Test that the manifest file is created."""
    manifest_dir = get_path("interim")
    if not manifest_dir.exists():
        try:
            manifest_dir = get_path("data_interim")
        except (ValueError, KeyError):
            manifest_dir = Path("data/interim")
    
    manifest_path = manifest_dir / "data_source_manifest.json"
    assert manifest_path.exists(), f"Manifest file not found at {manifest_path}"

def test_manifest_valid_json():
    """Test that the manifest is valid JSON."""
    manifest_dir = get_path("interim")
    if not manifest_dir.exists():
        try:
            manifest_dir = get_path("data_interim")
        except (ValueError, KeyError):
            manifest_dir = Path("data/interim")
    
    manifest_path = manifest_dir / "data_source_manifest.json"
    if not manifest_path.exists():
        pytest.skip("Manifest file does not exist yet.")
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    assert "dataset_id" in data
    assert "files" in data
    assert "verification_status" in data
    assert data["verification_status"] == "verified"

def test_manifest_structure():
    """Test the structure of the manifest."""
    manifest_dir = get_path("interim")
    if not manifest_dir.exists():
        try:
            manifest_dir = get_path("data_interim")
        except (ValueError, KeyError):
            manifest_dir = Path("data/interim")
    
    manifest_path = manifest_dir / "data_source_manifest.json"
    if not manifest_path.exists():
        pytest.skip("Manifest file does not exist yet.")
    
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    
    # Check required keys
    required_keys = ["dataset_id", "download_timestamp", "source", "destination", "total_files", "total_size_bytes", "files"]
    for key in required_keys:
        assert key in data, f"Missing key: {key}"
    
    # Check file structure
    if data["total_files"] > 0:
        assert len(data["files"]) == data["total_files"]
        file_entry = data["files"][0]
        assert "filename" in file_entry
        assert "sha256" in file_entry
        assert "size_bytes" in file_entry