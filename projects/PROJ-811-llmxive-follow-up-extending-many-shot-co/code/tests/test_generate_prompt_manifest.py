"""
Unit tests for generate_prompt_manifest.py

Tests cover:
- Directory scanning logic
- File naming pattern parsing
- Manifest generation and sorting
- Edge cases (empty dir, invalid names, missing dir)
"""

import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.scripts.generate_prompt_manifest import scan_prompt_directory, generate_manifest


@pytest.fixture
def temp_prompt_dir():
    """Create a temporary directory with sample prompt files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create valid prompt files
        valid_files = [
            ("42_logical_ascending.json", '{"seed": 42, "strategy": "logical_ascending"}'),
            ("42_logical_random.json", '{"seed": 42, "strategy": "logical_random"}'),
            ("42_original_cds.json", '{"seed": 42, "strategy": "original_cds"}'),
            ("128_logical_ascending.json", '{"seed": 128, "strategy": "logical_ascending"}'),
            ("128_logical_random.json", '{"seed": 128, "strategy": "logical_random"}'),
            ("128_original_cds.json", '{"seed": 128, "strategy": "original_cds"}'),
        ]
        
        for filename, content in valid_files:
            (tmpdir_path / filename).write_text(content)
        
        # Create invalid files (should be skipped)
        (tmpdir_path / "invalid_name.json").write_text("{}")  # Missing seed_strategy pattern
        (tmpdir_path / "abc_logical_ascending.json").write_text("{}")  # Non-numeric seed
        (tmpdir_path / ".hidden_file.json").write_text("{}")  # Hidden file
        
        yield tmpdir_path


@pytest.fixture
def temp_manifest_file():
    """Create a temporary file for manifest output."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        yield Path(f.name)
    # Cleanup happens after test
    if os.path.exists(f.name):
        os.remove(f.name)


def test_scan_prompt_directory_success(temp_prompt_dir):
    """Test successful scanning of a directory with valid prompt files."""
    results = scan_prompt_directory(temp_prompt_dir)
    
    assert len(results) == 6  # 6 valid files
    
    # Check structure
    for entry in results:
        assert "seed" in entry
        assert "strategy" in entry
        assert "file_path" in entry
        assert isinstance(entry["seed"], int)
        assert isinstance(entry["strategy"], str)
        assert Path(entry["file_path"]).exists()
    
    # Check specific entries
    seeds = {e["seed"] for e in results}
    strategies = {e["strategy"] for e in results}
    
    assert seeds == {42, 128}
    assert strategies == {"logical_ascending", "logical_random", "original_cds"}


def test_scan_prompt_directory_empty(temp_prompt_dir):
    """Test scanning an empty directory."""
    empty_dir = temp_prompt_dir / "empty_subdir"
    empty_dir.mkdir()
    
    results = scan_prompt_directory(empty_dir)
    assert len(results) == 0


def test_scan_prompt_directory_nonexistent():
    """Test scanning a non-existent directory."""
    non_existent = Path("/nonexistent/path/that/does/not/exist")
    results = scan_prompt_directory(non_existent)
    assert len(results) == 0


def test_scan_prompt_directory_invalid_format(temp_prompt_dir):
    """Test that invalid file formats are skipped."""
    results = scan_prompt_directory(temp_prompt_dir)
    
    # Should only have 6 valid entries, not the 3 invalid ones
    assert len(results) == 6
    
    # Verify invalid files are not included
    file_paths = {Path(e["file_path"]).name for e in results}
    assert "invalid_name.json" not in file_paths
    assert "abc_logical_ascending.json" not in file_paths
    assert ".hidden_file.json" not in file_paths


def test_generate_manifest(temp_prompt_dir, temp_manifest_file):
    """Test full manifest generation."""
    manifest = generate_manifest(temp_prompt_dir, temp_manifest_file)
    
    # Check manifest structure
    assert "generated_from" in manifest
    assert "total_entries" in manifest
    assert "entries" in manifest
    
    assert manifest["total_entries"] == 6
    assert len(manifest["entries"]) == 6
    
    # Check file was written
    assert temp_manifest_file.exists()
    written_content = json.loads(temp_manifest_file.read_text())
    assert written_content == manifest


def test_generate_manifest_sorting(temp_prompt_dir, temp_manifest_file):
    """Test that manifest entries are sorted by seed and strategy."""
    manifest = generate_manifest(temp_prompt_dir, temp_manifest_file)
    
    entries = manifest["entries"]
    
    # Check sorting: first by seed, then by strategy
    for i in range(len(entries) - 1):
        curr = entries[i]
        next_ = entries[i + 1]
        
        if curr["seed"] == next_["seed"]:
            assert curr["strategy"] <= next_["strategy"]
        else:
            assert curr["seed"] < next_["seed"]
    
    # First entry should be seed 42, logical_ascending (alphabetically first strategy)
    assert entries[0]["seed"] == 42
    assert entries[0]["strategy"] == "logical_ascending"
    
    # Last entry should be seed 128, original_cds (alphabetically last strategy)
    assert entries[-1]["seed"] == 128
    assert entries[-1]["strategy"] == "original_cds"


def test_generate_manifest_empty_directory(temp_manifest_file):
    """Test manifest generation with an empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        empty_dir = Path(tmpdir)
        manifest = generate_manifest(empty_dir, temp_manifest_file)
        
        assert manifest["total_entries"] == 0
        assert manifest["entries"] == []


def test_generate_manifest_creates_output_dir(temp_manifest_file):
    """Test that manifest generation creates output directory if needed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        deep_path = Path(tmpdir) / "deep" / "nested" / "dir" / "manifest.json"
        
        with tempfile.TemporaryDirectory() as src_tmpdir:
            src_dir = Path(src_tmpdir)
            (src_dir / "42_test.json").write_text("{}")
            
            manifest = generate_manifest(src_dir, deep_path)
            
            assert deep_path.exists()
            assert manifest["total_entries"] == 1