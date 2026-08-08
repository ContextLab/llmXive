"""
Unit tests for utils module.
"""

import pytest
import tempfile
import os
from pathlib import Path

# Test SHA-256 calculation
def test_calculate_sha256():
    """Test that SHA-256 hash is calculated correctly."""
    from utils.update_state import calculate_sha256
    
    # Create a temporary file with known content
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        hash_value = calculate_sha256(Path(temp_path))
        assert len(hash_value) == 64  # SHA-256 produces 64 hex characters
        assert all(c in '0123456789abcdef' for c in hash_value)
    finally:
        os.unlink(temp_path)

def test_scan_directory():
    """Test directory scanning and hashing."""
    from utils.update_state import scan_directory
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create some test files
        (tmpdir_path / "file1.txt").write_text("content1")
        (tmpdir_path / "file2.py").write_text("content2")
        (tmpdir_path / "subdir").mkdir()
        (tmpdir_path / "subdir" / "file3.txt").write_text("content3")
        
        # Scan without extension filter
        hashes = scan_directory(tmpdir_path)
        assert len(hashes) == 3
        assert "file1.txt" in hashes
        assert "file2.py" in hashes
        assert "subdir/file3.txt" in hashes
        
        # Scan with extension filter
        hashes_py = scan_directory(tmpdir_path, extensions=[".py"])
        assert len(hashes_py) == 1
        assert "file2.py" in hashes_py

def test_generate_fallback_scenes():
    """Test deterministic fallback scene generation."""
    from utils.create_scene_descriptions import generate_fallback_scenes
    
    # Generate scenes with fixed seed
    scenes1 = generate_fallback_scenes(n=10, seed=42)
    scenes2 = generate_fallback_scenes(n=10, seed=42)
    
    # Should be identical
    assert len(scenes1) == len(scenes2) == 10
    assert scenes1 == scenes2
    
    # Different seed should produce different results
    scenes3 = generate_fallback_scenes(n=10, seed=123)
    assert scenes1 != scenes3
    
    # Check structure
    for scene in scenes1:
        assert "scene_id" in scene
        assert "description" in scene
        assert scene["scene_id"].startswith("scene_")

def test_write_csv():
    """Test CSV writing functionality."""
    from utils.create_scene_descriptions import write_csv
    
    scenes = [
        {"scene_id": "scene_0001", "description": "A book on a table"},
        {"scene_id": "scene_0002", "description": "A cup next to a plate"}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_scenes.csv"
        write_csv(scenes, output_path)
        
        # Verify file exists
        assert output_path.exists()
        
        # Verify content
        content = output_path.read_text()
        assert "scene_id,description" in content
        assert "scene_0001" in content
        assert "A book on a table" in content
        assert "scene_0002" in content
        assert "A cup next to a plate" in content