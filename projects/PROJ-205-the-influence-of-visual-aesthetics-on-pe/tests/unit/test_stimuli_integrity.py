"""
Unit tests for Stimulus Content Hashing (T070).

Tests ensure that:
1. Hashes are computed correctly for stimulus files.
2. Stored hashes match the computed values.
3. Modifications to stimulus files are detected.
4. Missing or extra files trigger errors.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the module under test
# We use a relative import strategy that works in the test environment
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.stimuli_hash import (
    compute_file_sha256,
    compute_stimuli_hashes,
    save_stimuli_hashes,
    load_stored_hashes,
    verify_stimuli_integrity,
    initialize_stimuli_hashes,
    get_stimuli_files
)


@pytest.fixture
def temp_project_structure():
    """Create a temporary directory structure mimicking the project."""
    temp_root = tempfile.mkdtemp()
    stimuli_dir = Path(temp_root) / "stimuli"
    state_dir = Path(temp_root) / "state"
    stimuli_dir.mkdir()
    state_dir.mkdir()
    
    # Create dummy stimulus files
    (stimuli_dir / "professional.html").write_text("<html><body>Pro</body></html>")
    (stimuli_dir / "minimalist.html").write_text("<html><body>Mini</body></html>")
    (stimuli_dir / "low_quality.html").write_text("<html><body>Low</body></html>")
    (stimuli_dir / "neutral.html").write_text("<html><body>Neu</body></html>")
    
    # Create a non-HTML file to ensure it's ignored
    (stimuli_dir / "readme.txt").write_text("Readme")
    
    return {
        "root": Path(temp_root),
        "stimuli": stimuli_dir,
        "state": state_dir
    }


def test_compute_file_sha256(temp_project_structure):
    """Test that SHA-256 is computed correctly for a single file."""
    file_path = temp_project_structure["stimuli"] / "professional.html"
    hash_val = compute_file_sha256(file_path)
    
    assert len(hash_val) == 64  # SHA-256 hex length
    assert all(c in "0123456789abcdef" for c in hash_val)


def test_compute_stimuli_hashes(temp_project_structure):
    """Test that all HTML files are hashed and non-HTML ignored."""
    hashes = compute_stimuli_hashes(temp_project_structure["stimuli"])
    
    assert len(hashes) == 4
    assert "professional.html" in hashes
    assert "minimalist.html" in hashes
    assert "low_quality.html" in hashes
    assert "neutral.html" in hashes
    assert "readme.txt" not in hashes


def test_save_and_load_hashes(temp_project_structure):
    """Test saving and loading hashes from JSON."""
    hashes = compute_stimuli_hashes(temp_project_structure["stimuli"])
    
    save_stimuli_hashes(hashes, temp_project_structure["state"])
    
    loaded = load_stored_hashes(temp_project_structure["state"])
    
    assert loaded == hashes


def test_verify_integrity_success(temp_project_structure):
    """Test that verification passes when files match stored hashes."""
    # Initialize
    initialize_stimuli_hashes(temp_project_structure["stimuli"], temp_project_structure["state"])
    
    # Verify should pass
    result = verify_stimuli_integrity(temp_project_structure["stimuli"], temp_project_structure["state"])
    assert result is True


def test_verify_integrity_failure_on_modification(temp_project_structure):
    """Test that verification fails if a stimulus file is modified."""
    # Initialize
    initialize_stimuli_hashes(temp_project_structure["stimuli"], temp_project_structure["state"])
    
    # Modify a file
    modified_file = temp_project_structure["stimuli"] / "professional.html"
    modified_file.write_text("<html><body>PRO MODIFIED</body></html>")
    
    # Verify should raise RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        verify_stimuli_integrity(temp_project_structure["stimuli"], temp_project_structure["state"])
    
    assert "Hash mismatch" in str(excinfo.value)
    assert "professional.html" in str(excinfo.value)


def test_verify_integrity_failure_on_missing_file(temp_project_structure):
    """Test that verification fails if a stimulus file is missing."""
    # Initialize
    initialize_stimuli_hashes(temp_project_structure["stimuli"], temp_project_structure["state"])
    
    # Remove a file
    (temp_project_structure["stimuli"] / "minimalist.html").unlink()
    
    # Verify should raise RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        verify_stimuli_integrity(temp_project_structure["stimuli"], temp_project_structure["state"])
    
    assert "missing" in str(excinfo.value).lower()
    assert "minimalist.html" in str(excinfo.value)


def test_verify_integrity_failure_on_extra_file(temp_project_structure):
    """Test that verification fails if an unexpected stimulus file is present."""
    # Initialize
    initialize_stimuli_hashes(temp_project_structure["stimuli"], temp_project_structure["state"])
    
    # Add a new file
    (temp_project_structure["stimuli"] / "new_stimulus.html").write_text("<html>New</html>")
    
    # Verify should raise RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        verify_stimuli_integrity(temp_project_structure["stimuli"], temp_project_structure["state"])
    
    assert "Unexpected" in str(excinfo.value)
    assert "new_stimulus.html" in str(excinfo.value)


def test_get_stimuli_files_ignores_non_html(temp_project_structure):
    """Test that non-HTML files are ignored."""
    files = get_stimuli_files(temp_project_structure["stimuli"])
    names = [f.name for f in files]
    
    assert "readme.txt" not in names
    assert len(names) == 4


def test_initialize_creates_state_file(temp_project_structure):
    """Test that initialize creates the state file."""
    state_file = temp_project_structure["state"] / "stimuli_hashes.json"
    assert not state_file.exists()
    
    initialize_stimuli_hashes(temp_project_structure["stimuli"], temp_project_structure["state"])
    
    assert state_file.exists()
    
    # Check content structure
    with open(state_file, "r") as f:
        data = json.load(f)
    
    assert "stimuli_hashes" in data
    assert len(data["stimuli_hashes"]) == 4
