import pytest
import yaml
from pathlib import Path
from llmxive_toolkit import paths
from code.utils.checksums import generate_checksums

def test_generate_checksums_creates_file():
    """Verify that generate_checksums creates the manifest and records hashes."""
    # Setup: create a dummy raw file
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    test_file = raw_dir / "test_checksum_file.txt"
    test_file.write_text("checksum test content", encoding="utf-8")
    
    manifest_path = paths.logs("raw_checksums.yaml")
    # Ensure clean state
    if manifest_path.exists():
        manifest_path.unlink()
    
    try:
        # Execute
        generate_checksums(raw_root=raw_dir, state_file=manifest_path)
        
        # Verify
        assert manifest_path.exists()
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        assert "artifact_hashes" in data
        # The path should be stored relative to project root
        rel_path = test_file.relative_to(paths.root).as_posix()
        assert rel_path in data["artifact_hashes"]
        assert len(data["artifact_hashes"][rel_path]) == 64  # SHA-256 length
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
        if manifest_path.exists():
            manifest_path.unlink()

def test_generate_checksums_updates_existing():
    """Verify that generate_checksums merges with existing manifest data."""
    manifest_path = paths.logs("raw_checksums.yaml")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    existing_data = {
        "artifact_hashes": {"old_file.csv": "oldhash"},
        "metadata": {"version": "1.0"}
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.dump(existing_data, f)
        
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    test_file = raw_dir / "new_file.txt"
    test_file.write_text("new content", encoding="utf-8")
    
    try:
        generate_checksums(raw_root=raw_dir, state_file=manifest_path)
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        # Check that old metadata is preserved
        assert data["metadata"]["version"] == "1.0"
        # Check that new file is added
        rel_path = test_file.relative_to(paths.root).as_posix()
        assert rel_path in data["artifact_hashes"]
        # Check that old hash is still there
        assert "old_file.csv" in data["artifact_hashes"]
    finally:
        if test_file.exists():
            test_file.unlink()
        if manifest_path.exists():
            manifest_path.unlink()