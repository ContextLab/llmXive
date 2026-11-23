"""
Unit tests for the paradigm_loader module.
"""

import json
import tempfile
from pathlib import Path

import pytest

from code.download.paradigm_loader import (
    ParadigmLoaderError,
    load_paradigm_manifest,
    parse_research_manifest,
)


def test_parse_valid_manifest():
    """Test parsing a valid research.md file."""
    content = """
    # Research Manifest
    
    ### Paradigm List
    - [ ] Task 1: paradigm: Motor dataset_id: ds000030
    - [ ] Task 2: paradigm: Visual dataset_id: ds000031
    - [ ] Task 3: paradigm: Auditory dataset_id: ds000032
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)
    
    try:
        results = parse_research_manifest(temp_path)
        assert len(results) == 3
        assert results[0] == {"paradigm": "Motor", "dataset_id": "ds000030"}
        assert results[1] == {"paradigm": "Visual", "dataset_id": "ds000031"}
        assert results[2] == {"paradigm": "Auditory", "dataset_id": "ds000032"}
    finally:
        temp_path.unlink()


def test_parse_manifest_limit():
    """Test that the parser respects the MAX_PARADIGMS limit."""
    # Create a list of 20 paradigms
    lines = ["# Research Manifest\n"]
    for i in range(20):
        lines.append(f"- [ ] Task {i}: paradigm: Task_{i} dataset_id: ds0000{i:02d}\n")
    
    content = "\n".join(lines)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)
    
    try:
        results = parse_research_manifest(temp_path)
        # Should be truncated to 15 (MAX_PARADIGMS)
        assert len(results) == 15
    finally:
        temp_path.unlink()


def test_parse_manifest_no_entries():
    """Test parsing a file with no valid entries."""
    content = """
    # Research Manifest
    This is just text.
    No paradigms here.
    """
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)
    
    try:
        with pytest.raises(ParadigmLoaderError):
            parse_research_manifest(temp_path)
    finally:
        temp_path.unlink()


def test_parse_manifest_file_not_found():
    """Test parsing a non-existent file."""
    with pytest.raises(ParadigmLoaderError):
        parse_research_manifest(Path("non_existent_file.md"))


def test_load_paradigm_manifest_default():
    """Test the main load function with default path (should fail if file missing)."""
    # This test assumes the default path doesn't exist in the test environment
    # or we mock it. Since we can't guarantee the file exists in the test env,
    # we test the error handling or use a temp file if we wanted to test success.
    # For now, we assume the default path might not exist.
    # Let's create a temp file and test with it.
    content = "- [ ] Task: paradigm: Test dataset_id: ds000099\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = Path(f.name)
    
    try:
        results = load_paradigm_manifest(manifest_path=temp_path)
        assert len(results) == 1
        assert results[0]["paradigm"] == "Test"
    finally:
        temp_path.unlink()
