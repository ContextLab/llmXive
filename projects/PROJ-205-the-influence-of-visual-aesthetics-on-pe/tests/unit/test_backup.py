"""
Unit tests for the Automated Data Backup Module (T072).
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest

# Import the module under test
from code.utils.backup import (
    get_project_root,
    get_submissions_csv_path,
    get_backup_dir,
    create_backup,
    backup_on_write
)


@pytest.fixture
def temp_project_structure():
    """
    Create a temporary directory structure mimicking the project layout
    to test backup functionality in isolation.
    """
    # Create a temp root
    temp_root = Path(tempfile.mkdtemp())

    # Create necessary subdirectories
    data_raw = temp_root / "data" / "raw"
    data_backups = temp_root / "data" / "backups"
    data_raw.mkdir(parents=True, exist_ok=True)
    data_backups.mkdir(parents=True, exist_ok=True)

    # Create a mock submissions.csv
    mock_csv = data_raw / "submissions.csv"
    mock_csv.write_text("participant_id,age,education\n1,25,Bachelor\n2,30,Master\n")

    # Yield the temp root
    yield temp_root

    # Cleanup
    shutil.rmtree(temp_root)


def test_get_project_root():
    """Test that get_project_root returns the correct path structure."""
    root = get_project_root()
    assert isinstance(root, Path)
    assert root.name == "PROJ-205-the-influence-of-visual-aesthetics-on-pe"


def test_create_backup_success(temp_project_structure):
    """Test that create_backup successfully copies the file and creates a manifest."""
    source_path = temp_project_structure / "data" / "raw" / "submissions.csv"
    
    # Override the internal path logic for the test by passing explicit path
    # We need to patch the internal functions or pass the path directly to create_backup
    # Since create_backup accepts an optional source_path, we pass it.
    
    backup_path = create_backup(source_path)
    
    assert backup_path is not None
    assert backup_path.exists()
    assert backup_path.suffix == ".csv"
    assert backup_path.parent.name == "backups"
    
    # Verify content matches
    assert source_path.read_text() == backup_path.read_text()
    
    # Verify manifest creation
    manifest_path = temp_project_structure / "data" / "backups" / "backup_manifest.json"
    assert manifest_path.exists()
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    assert len(manifest) == 1
    assert manifest[0]["backup_file"] == str(backup_path)
    assert "timestamp" in manifest[0]


def test_create_backup_file_not_found():
    """Test that create_backup raises FileNotFoundError for missing source."""
    fake_path = Path("/non/existent/path/file.csv")
    with pytest.raises(FileNotFoundError):
        create_backup(fake_path)


def test_backup_on_write_success(temp_project_structure):
    """Test that backup_on_write triggers a backup successfully."""
    source_path = temp_project_structure / "data" / "raw" / "submissions.csv"
    
    result = backup_on_write(source_path)
    
    assert result is True
    
    # Verify a backup was created
    backup_dir = temp_project_structure / "data" / "backups"
    backups = list(backup_dir.glob("submissions_*.csv"))
    assert len(backups) >= 1


def test_backup_on_write_failure():
    """Test that backup_on_write raises an error if backup fails."""
    fake_path = Path("/non/existent/path/file.csv")
    with pytest.raises(FileNotFoundError):
        backup_on_write(fake_path)
