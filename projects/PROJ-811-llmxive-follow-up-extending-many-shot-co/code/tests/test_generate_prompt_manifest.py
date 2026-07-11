"""
Tests for the prompt manifest generation script (T028).

These tests verify that:
1. The manifest generator correctly scans prompt directories
2. Metadata is extracted from filenames and file contents
3. The output manifest is correctly formatted
"""
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from code.scripts.generate_prompt_manifest import (
    scan_prompt_directory,
    generate_manifest
)

@pytest.fixture
def temp_prompt_dir():
    """Create a temporary directory with sample prompt files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        prompt_dir = Path(tmpdir)
        
        # Create sample prompt files
        sample_prompts = [
            ("prompts_seed_42_logical_ascending.json", {"seed": 42, "strategy": "logical_ascending", "prompts": ["p1", "p2", "p3"]}),
            ("prompts_seed_42_logical_random.json", {"seed": 42, "strategy": "logical_random", "prompts": ["p1", "p2"]}),
            ("prompts_seed_42_original_cds.json", {"seed": 42, "strategy": "original_cds", "prompts": ["p1"]}),
            ("prompts_seed_123_logical_ascending.json", {"seed": 123, "strategy": "logical_ascending", "prompts": ["p1", "p2"]}),
        ]
        
        for filename, data in sample_prompts:
            with open(prompt_dir / filename, 'w') as f:
                json.dump(data, f)
        
        # Add an invalid filename that should be skipped
        with open(prompt_dir / "invalid_filename.txt", 'w') as f:
            f.write("should be ignored")
        
        yield prompt_dir

def test_scan_prompt_directory_success(temp_prompt_dir):
    """Test successful scanning of prompt directory."""
    entries = scan_prompt_directory(temp_prompt_dir)
    
    assert len(entries) == 4
    
    # Check first entry
    first = entries[0]
    assert first["seed"] == 42
    assert first["strategy"] == "logical_ascending"
    assert first["prompt_count"] == 3
    assert first["file_path"].endswith("prompts_seed_42_logical_ascending.json")

def test_scan_prompt_directory_empty():
    """Test scanning empty directory returns empty list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        entries = scan_prompt_directory(Path(tmpdir))
        assert len(entries) == 0

def test_scan_prompt_directory_nonexistent():
    """Test scanning non-existent directory returns empty list."""
    entries = scan_prompt_directory(Path("/nonexistent/path"))
    assert len(entries) == 0

def test_scan_prompt_directory_invalid_format(temp_prompt_dir):
    """Test that invalid filenames are skipped."""
    entries = scan_prompt_directory(temp_prompt_dir)
    
    # Should only have valid entries
    for entry in entries:
        assert entry["strategy"] in ["logical_ascending", "logical_random", "original_cds"]
        assert entry["seed"] in [42, 123]

def test_generate_manifest(temp_prompt_dir, temp_output_dir):
    """Test manifest generation from prompt directory."""
    output_path = temp_output_dir / "prompt_manifest.json"
    
    manifest = generate_manifest(temp_prompt_dir, output_path)
    
    assert manifest["total_files"] == 4
    assert manifest["total_prompts"] == 8  # 3+2+1+2
    assert len(manifest["entries"]) == 4
    
    # Verify output file exists
    assert output_path.exists()
    
    # Verify JSON structure
    with open(output_path) as f:
        loaded = json.load(f)
    assert loaded["total_files"] == 4
    assert "entries" in loaded

def test_generate_manifest_sorting(temp_prompt_dir, temp_output_dir):
    """Test that manifest entries are sorted by seed then strategy."""
    output_path = temp_output_dir / "prompt_manifest.json"
    
    manifest = generate_manifest(temp_prompt_dir, output_path)
    
    entries = manifest["entries"]
    for i in range(len(entries) - 1):
        curr = entries[i]
        next_entry = entries[i + 1]
        
        if curr["seed"] == next_entry["seed"]:
            assert curr["strategy"] <= next_entry["strategy"]
        else:
            assert curr["seed"] <= next_entry["seed"]
