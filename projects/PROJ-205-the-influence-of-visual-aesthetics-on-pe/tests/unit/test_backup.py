"""
Unit tests for the automated data backup module (T072).

Tests verify that:
1. Backup file is created with correct timestamped naming convention.
2. Backup content matches the source file exactly.
3. Backup manifest is updated correctly.
4. Appropriate errors are raised when source file is missing.
"""

import os
import csv
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the module under test
import sys
from unittest.mock import patch

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.backup import (
    create_backup,
    get_backup_dir,
    get_submissions_csv_path,
    backup_on_write
)


class TestBackupCreation:
    """Tests for backup creation functionality."""

    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create a temporary data directory structure with a mock submissions file."""
        # Setup temporary directory structure
        data_raw = tmp_path / "data" / "raw"
        data_raw.mkdir(parents=True)

        # Create a mock submissions.csv
        submissions_file = data_raw / "submissions.csv"
        with open(submissions_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['participant_id', 'age', 'education', 'timestamp'])
            writer.writerow(['uuid-1234', '25', 'Bachelor', '2024-01-01T10:00:00'])
            writer.writerow(['uuid-5678', '30', 'Master', '2024-01-01T10:05:00'])

        return {
            'temp_root': tmp_path,
            'submissions_file': submissions_file,
            'backup_dir': tmp_path / "data" / "backups"
        }

    def test_backup_file_created(self, temp_data_dir, tmp_path):
        """Test that a backup file is created with correct naming convention."""
        # Patch the path functions to use our temp directory
        with patch('code.utils.backup.get_project_root', return_value=temp_data_dir['temp_root']):
            backup_path = create_backup(temp_data_dir['submissions_file'])

            # Verify backup file exists
            assert backup_path.exists()
            assert backup_path.parent == temp_data_dir['backup_dir']

            # Verify naming convention: submissions_YYYYMMDD_HHMMSS.csv
            assert backup_path.name.startswith('submissions_')
            assert backup_path.name.endswith('.csv')
            assert len(backup_path.name) == len('submissions_20240101_120000.csv')

    def test_backup_content_matches_source(self, temp_data_dir, tmp_path):
        """Test that backup content is identical to source."""
        with patch('code.utils.backup.get_project_root', return_value=temp_data_dir['temp_root']):
            backup_path = create_backup(temp_data_dir['submissions_file'])

            # Read source and backup
            with open(temp_data_dir['submissions_file'], 'r') as f:
                source_content = f.read()
            with open(backup_path, 'r') as f:
                backup_content = f.read()

            assert source_content == backup_content

    def test_backup_manifest_created(self, temp_data_dir, tmp_path):
        """Test that the backup manifest is created and updated."""
        with patch('code.utils.backup.get_project_root', return_value=temp_data_dir['temp_root']):
            create_backup(temp_data_dir['submissions_file'])

            manifest_path = temp_data_dir['backup_dir'] / "backup_manifest.json"
            assert manifest_path.exists()

            with open(manifest_path, 'r') as f:
                manifest = json.load(f)

            assert isinstance(manifest, list)
            assert len(manifest) == 1
            assert 'timestamp' in manifest[0]
            assert 'source_file' in manifest[0]
            assert 'backup_file' in manifest[0]
            assert 'backup_filename' in manifest[0]

    def test_missing_source_file_raises_error(self, temp_data_dir, tmp_path):
        """Test that FileNotFoundError is raised when source file is missing."""
        with patch('code.utils.backup.get_project_root', return_value=temp_data_dir['temp_root']):
            missing_file = temp_data_dir['temp_root'] / "data" / "raw" / "nonexistent.csv"
            with pytest.raises(FileNotFoundError, match="Source file not found"):
                create_backup(missing_file)

    def test_backup_on_write_success(self, temp_data_dir, tmp_path):
        """Test the backup_on_write wrapper function."""
        with patch('code.utils.backup.get_project_root', return_value=temp_data_dir['temp_root']):
            result = backup_on_write(temp_data_dir['submissions_file'])
            assert result is True

            # Verify a backup was actually created
            backup_dir = temp_data_dir['backup_dir']
            assert len(list(backup_dir.glob("submissions_*.csv"))) >= 1

    def test_multiple_backups_create_separate_files(self, temp_data_dir, tmp_path):
        """Test that multiple backups create separate timestamped files."""
        with patch('code.utils.backup.get_project_root', return_value=temp_data_dir['temp_root']):
            # Create first backup
            backup1 = create_backup(temp_data_dir['submissions_file'])
            # Small delay to ensure different timestamp
            import time
            time.sleep(1.1)
            # Create second backup
            backup2 = create_backup(temp_data_dir['submissions_file'])

            assert backup1 != backup2
            assert backup1.exists()
            assert backup2.exists()

            # Verify manifest has two entries
            manifest_path = temp_data_dir['backup_dir'] / "backup_manifest.json"
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            assert len(manifest) == 2

    def test_backup_directory_created_if_missing(self, temp_data_dir, tmp_path):
        """Test that backup directory is created if it doesn't exist."""
        # Remove the backup directory to test creation
        backup_dir = temp_data_dir['backup_dir']
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

        with patch('code.utils.backup.get_project_root', return_value=temp_data_dir['temp_root']):
            backup_path = create_backup(temp_data_dir['submissions_file'])

            assert backup_dir.exists()
            assert backup_path.exists()