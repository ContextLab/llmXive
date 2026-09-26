import os
import yaml
import csv
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to mock the utils import if it's not available in test environment
# But since we are writing a test for the module, we assume the module is importable
# and utils is available in the code path or we mock it.
# For this test, we will patch the ensure_directory function behavior or run it in a temp dir.

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure to simulate the project root."""
    temp_dir = tempfile.mkdtemp()
    # Create the expected relative structure
    base = Path(temp_dir)
    (base / "data").mkdir()
    (base / "state" / "projects").mkdir(parents=True)
    yield base
    shutil.rmtree(temp_dir)

def test_ensure_directory(temp_project_root):
    from data_setup import ensure_directory
    
    new_dir = temp_project_root / "data" / "raw"
    assert not new_dir.exists()
    ensure_directory(str(new_dir))
    assert new_dir.exists()

def test_initialize_checksums_file(temp_project_root):
    from data_setup import initialize_checksums_file
    
    checksums_file = temp_project_root / "data" / "checksums.txt"
    initialize_checksums_file(str(checksums_file))
    
    assert checksums_file.exists()
    with open(checksums_file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        assert header == ['filename', 'hash']

def test_initialize_state_file(temp_project_root):
    from data_setup import initialize_state_file
    
    state_file = temp_project_root / "state" / "projects" / "PROJ-334-predicting-avian-song-variation-with-cli.yaml"
    initialize_state_file(str(state_file))
    
    assert state_file.exists()
    with open(state_file, 'r') as f:
        data = yaml.safe_load(f)
        assert 'artifact_hashes' in data
        assert data['artifact_hashes'] == {}