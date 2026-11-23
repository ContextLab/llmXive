"""
Tests for the asset generation script.
"""
import os
import sys
import json
import hashlib
from pathlib import Path
import pytest
from PIL import Image

# Add parent to path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.generate_assets import get_project_root, ensure_dirs, compute_sha256, create_technical_diagram, generate_assets

def test_get_project_root():
    root = get_project_root()
    assert root.exists()
    assert root.name == "PROJ-821-llmxive-follow-up-extending-training-lon" or "llmxive" in str(root).lower()

def test_ensure_dirs():
    assets_dir = ensure_dirs()
    assert assets_dir.exists()
    assert assets_dir.is_dir()

def test_compute_sha256(tmp_path):
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")
    hash_val = compute_sha256(test_file)
    # SHA256 of "hello world"
    expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert hash_val == expected

def test_create_technical_diagram(tmp_path):
    output_path = tmp_path / "test_img.png"
    create_technical_diagram(0, output_path)
    assert output_path.exists()
    
    with Image.open(output_path) as img:
        assert img.size == (336, 336)
        assert img.mode == 'L'

def test_generate_assets_integration(tmp_path, monkeypatch):
    # Monkeypatch the ensure_dirs to use tmp_path for isolation
    def mock_ensure_dirs():
        assets_dir = tmp_path / "data" / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        return assets_dir
    
    monkeypatch.setattr("scripts.generate_assets.ensure_dirs", mock_ensure_dirs)
    
    # Also need to monkeypatch get_project_root if it's used for path construction in other places
    # But generate_assets uses ensure_dirs mostly.
    
    manifest = generate_assets()
    
    assert manifest["count"] == 20
    assert len(manifest["images"]) == 20
    
    # Check manifest file existence
    manifest_path = tmp_path / "data" / "assets" / "manifest.json"
    assert manifest_path.exists()
    
    # Verify dimensions and hashes in manifest
    for img_entry in manifest["images"]:
        assert img_entry["dimensions"] == [336, 336]
        assert "sha256" in img_entry
        assert img_entry["size_bytes"] > 0
        
        # Verify the file actually exists and hash matches
        img_path = tmp_path / "data" / "assets" / img_entry["filename"]
        assert img_path.exists()
        with Image.open(img_path) as img:
            assert img.size == (336, 336)
        
        # Re-compute hash to verify
        computed_hash = compute_sha256(img_path)
        assert computed_hash == img_entry["sha256"]