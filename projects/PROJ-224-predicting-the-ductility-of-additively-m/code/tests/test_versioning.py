import os
import sys
import tempfile
import hashlib
import pytest
import yaml
from pathlib import Path

# Add the project root to the path if necessary for imports
# Assuming tests run from the project root
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.versioning import compute_sha256, version_artifact

def test_compute_sha256():
    """Test SHA-256 computation on a known string."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name

    try:
        expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
        computed_hash = compute_sha256(temp_path)
        assert computed_hash == expected_hash, f"Hash mismatch: {computed_hash} != {expected_hash}"
    finally:
        os.unlink(temp_path)

def test_compute_sha256_missing_file():
    """Test that compute_sha256 raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        compute_sha256("/nonexistent/path/file.txt")

def test_version_artifact():
    """Test the full versioning workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy CSV
        csv_path = Path(tmpdir) / "test_data.csv"
        csv_path.write_text("col1,col2\n1,2\n3,4")
        
        # Create state directory structure
        state_dir = Path(tmpdir) / "state" / "projects"
        state_dir.mkdir(parents=True)
        state_path = state_dir / "test_project.yaml"

        # Run versioning
        success = version_artifact(str(csv_path), str(state_path))
        
        assert success is True, "Versioning failed"
        assert state_path.exists(), "State file was not created"

        # Verify content
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f)

        assert 'artifact_hashes' in state_data
        assert 'test_data.csv' in state_data['artifact_hashes']
        
        entry = state_data['artifact_hashes']['test_data.csv']
        assert entry['path'] == str(csv_path)
        
        # Verify hash correctness
        expected_hash = hashlib.sha256(b"col1,col2\n1,2\n3,4").hexdigest()
        assert entry['sha256'] == expected_hash

def test_version_artifact_overwrite():
    """Test that versioning updates the hash if the file content changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = Path(tmpdir) / "test_data.csv"
        state_dir = Path(tmpdir) / "state" / "projects"
        state_dir.mkdir(parents=True)
        state_path = state_dir / "test_project.yaml"

        # First write
        csv_path.write_text("data v1")
        version_artifact(str(csv_path), str(state_path))

        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f)
        old_hash = state_data['artifact_hashes']['test_data.csv']['sha256']

        # Change content
        csv_path.write_text("data v2")
        version_artifact(str(csv_path), str(state_path))

        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f)
        new_hash = state_data['artifact_hashes']['test_data.csv']['sha256']

        assert old_hash != new_hash, "Hash should have changed"
        assert new_hash == hashlib.sha256(b"data v2").hexdigest()