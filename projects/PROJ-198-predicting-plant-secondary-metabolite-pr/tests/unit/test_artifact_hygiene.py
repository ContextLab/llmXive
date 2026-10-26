import pytest
import yaml
from pathlib import Path
from llmxive_toolkit import paths
from code.utils.artifact import record_artifacts, track_path, STATE_FILE

def test_sha256_computation(tmp_path):
    """Test that record_artifacts correctly hashes a file and saves it to state."""
    # Create a dummy file
    test_file = tmp_path / "test_artifact.txt"
    content = b"hello world"
    test_file.write_bytes(content)
    
    # Record it
    record_artifacts([test_file])
    
    # Verify state file exists and contains the hash
    assert STATE_FILE.exists()
    with STATE_FILE.open("rt") as f:
        state = yaml.safe_load(f)
    
    # The key should be the relative path from root
    rel_path = str(test_file.resolve().relative_to(paths.root))
    assert rel_path in state
    
    # Manually compute expected hash
    import hashlib
    expected_hash = hashlib.sha256(content).hexdigest()
    assert state[rel_path] == expected_hash

def test_track_path_atexit(tmp_path, monkeypatch):
    """Test that track_path registers a file for recording on exit."""
    # We can't easily trigger atexit in a test without exiting the process,
    # so we test the internal list.
    import code.utils.artifact as artifact
    
    test_file = tmp_path / "tracked.txt"
    test_file.write_text("tracked content")
    
    artifact._PENDING_PATHS.clear()
    track_path(test_file)
    
    assert test_file.resolve() in artifact._PENDING_PATHS

def test_record_missing_file():
    """Test that record_artifacts raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        record_artifacts([paths.data("non_existent_file.csv")])