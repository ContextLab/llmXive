"""
Unit tests for the state update module (T038).
"""
import os
import sys
import tempfile
import yaml
from pathlib import Path
import hashlib
import pytest

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from update_state import calculate_sha256, load_state, update_state, STATE_FILE, STATE_DIR

@pytest.fixture
def temp_state_file():
    """Create a temporary state file for testing."""
    # Use a temp directory to avoid polluting the actual project state
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_state_dir = Path(tmpdir) / "state" / "projects"
        temp_state_dir.mkdir(parents=True, exist_ok=True)
        temp_file = temp_state_dir / "PROJ-332-exploring-the-influence-of-network-topol.yaml"
        
        # Create initial state
        initial_state = {
            "project_id": "PROJ-332-exploring-the-influence-of-network-topol",
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
            "artifact_hashes": {},
            "tasks_completed": [],
            "last_run": None
        }
        with open(temp_file, "w") as f:
            yaml.dump(initial_state, f)
        
        yield temp_file

@pytest.fixture
def temp_artifact_file():
    """Create a temporary artifact file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
        f.write("seed,N,p,avg_degree,conductivity,percolation_flag,scaling_factor\n")
        f.write("1,100,0.1,4.5,120.5,1,1.0\n")
        f.write("2,100,0.1,4.6,125.0,1,1.05\n")
        yield f.name
    # Cleanup handled by pytest or manually

def test_calculate_sha256(temp_artifact_file):
    """Test that SHA-256 is calculated correctly."""
    # Calculate expected hash manually
    sha256_hash = hashlib.sha256()
    with open(temp_artifact_file, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    expected_hash = sha256_hash.hexdigest()
    
    # Compare with function output
    actual_hash = calculate_sha256(temp_artifact_file)
    assert actual_hash == expected_hash
    assert len(actual_hash) == 64  # SHA-256 hex length

def test_calculate_sha256_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        calculate_sha256("/nonexistent/path/file.csv")

def test_load_state_initializes_if_missing(temp_state_file):
    """Test that load_state initializes state if file is missing."""
    # Delete the temp file
    os.remove(temp_state_file)
    
    # Load should create it
    state = load_state()
    assert "project_id" in state
    assert "artifact_hashes" in state
    assert "tasks_completed" in state
    assert os.path.exists(temp_state_file)

def test_update_state_calculates_hash(temp_state_file, temp_artifact_file):
    """Test that update_state correctly calculates and stores hash."""
    # Temporarily override STATE_FILE for this test
    import update_state
    original_state_file = update_state.STATE_FILE
    update_state.STATE_FILE = temp_state_file
    
    try:
        result = update_state("simulation_results.csv", temp_artifact_file, task_id="T038")
        
        assert "artifact_hashes" in result
        assert "simulation_results.csv" in result["artifact_hashes"]
        
        hash_info = result["artifact_hashes"]["simulation_results.csv"]
        assert "hash" in hash_info
        assert "path" in hash_info
        assert "updated_at" in hash_info
        
        # Verify hash correctness
        expected_hash = calculate_sha256(temp_artifact_file)
        assert hash_info["hash"] == expected_hash
        
        # Verify task_id was recorded
        assert "T038" in result["tasks_completed"]
    finally:
        update_state.STATE_FILE = original_state_file

def test_update_state_missing_artifact(temp_state_file):
    """Test that update_state raises FileNotFoundError for missing artifact."""
    import update_state
    original_state_file = update_state.STATE_FILE
    update_state.STATE_FILE = temp_state_file
    
    try:
        with pytest.raises(FileNotFoundError):
            update_state("missing.csv", "/nonexistent/path.csv")
    finally:
        update_state.STATE_FILE = original_state_file

def test_update_state_updates_timestamp(temp_state_file, temp_artifact_file):
    """Test that update_state updates the timestamp."""
    import update_state
    original_state_file = update_state.STATE_FILE
    update_state.STATE_FILE = temp_state_file
    
    try:
        result = update_state("test.csv", temp_artifact_file)
        
        assert "updated_at" in result
        assert "last_run" in result
        # Timestamps should be ISO format strings
        assert "T" in result["updated_at"]
        assert "T" in result["last_run"]
    finally:
        update_state.STATE_FILE = original_state_file
