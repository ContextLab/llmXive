import pytest
import yaml
import tempfile
from pathlib import Path
import os

from ingestion.update_state import load_checksums, load_or_create_state, update_state_with_checksums, save_state

def test_load_checksums_empty_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("")
        temp_path = Path(f.name)
    
    try:
        result = load_checksums(temp_path)
        assert result == {}
    finally:
        os.unlink(temp_path)

def test_load_checksums_valid():
    content = """# Checksums
a1b2c3d4e5f6  data/raw/sample.csv
9876543210ab  data/intermediate/merged.csv
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(content)
        temp_path = Path(f.name)
    
    try:
        result = load_checksums(temp_path)
        assert len(result) == 2
        assert result["data/raw/sample.csv"] == "a1b2c3d4e5f6"
        assert result["data/intermediate/merged.csv"] == "9876543210ab"
    finally:
        os.unlink(temp_path)

def test_load_or_create_state_new():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "state.yaml"
        state = load_or_create_state(state_path)
        
        assert "project_id" in state
        assert "artifacts" in state
        assert state["artifacts"] == {}

def test_update_state_with_checksums():
    state = load_or_create_state(Path("/tmp/fake.yaml"))
    checksums = {
        "data/intermediate/merged.csv": "abc123"
    }
    
    # Mock project root
    project_root = Path("/mock/root")
    
    # We need to ensure the file "exists" for the logic to pass the existence check
    # In this unit test, we can't easily mock Path.exists() without patching, 
    # so we assume the function logic handles it or we test the dictionary manipulation directly.
    # However, the function checks existence. Let's patch the existence check or assume the path logic works.
    # For a pure unit test of the dictionary logic, we might need to refactor slightly, 
    # but let's test the happy path where we create a temp file structure.
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create the file that the checksum refers to
        (tmp_path / "data" / "intermediate").mkdir(parents=True, exist_ok=True)
        (tmp_path / "data" / "intermediate" / "merged.csv").touch()
        
        new_state = update_state_with_checksums(state, checksums, tmp_path)
        
        assert "data/intermediate/merged.csv" in new_state["artifacts"]
        assert new_state["artifacts"]["data/intermediate/merged.csv"]["sha256"] == "abc123"
        assert "last_verified" in new_state["artifacts"]["data/intermediate/merged.csv"]