"""
Unit tests for T014b: update_artifact_hashes functionality.
"""
import os
import csv
import yaml
import tempfile
import shutil
import pytest
from pathlib import Path
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.update_artifact_hashes import load_checksums, update_project_state

class TestLoadChecksums:
    def test_load_valid_checksums(self, tmp_path):
        """Test loading a valid checksums CSV"""
        csv_path = tmp_path / "checksums.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'sha256'])
            writer.writerow(['dataset1.csv', 'abc123def456'])
            writer.writerow(['dataset2.csv', '789xyz000'])
        
        result = load_checksums(str(csv_path))
        assert len(result) == 2
        assert result['dataset1.csv'] == 'abc123def456'
        assert result['dataset2.csv'] == '789xyz000'

    def test_load_missing_file(self, tmp_path):
        """Test loading from a non-existent file returns empty dict"""
        result = load_checksums(str(tmp_path / "nonexistent.csv"))
        assert result == {}

    def test_load_with_empty_rows(self, tmp_path):
        """Test loading CSV with empty values handles gracefully"""
        csv_path = tmp_path / "checksums.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'sha256'])
            writer.writerow(['', 'abc123'])  # Empty filename
            writer.writerow(['dataset.csv', ''])  # Empty sha256
            writer.writerow(['valid.csv', 'validhash'])
        
        result = load_checksums(str(csv_path))
        assert len(result) == 1
        assert 'valid.csv' in result

class TestUpdateProjectState:
    def test_create_new_state_file(self, tmp_path):
        """Test creating a new state file with checksums"""
        state_path = tmp_path / "state.yaml"
        checksums = {'file1.csv': 'hash1', 'file2.csv': 'hash2'}
        
        update_project_state(str(state_path), checksums)
        
        assert state_path.exists()
        with open(state_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert 'artifact_hashes' in data
        assert data['artifact_hashes'] == checksums
        assert 'last_updated' in data

    def test_update_existing_state_file(self, tmp_path):
        """Test updating an existing state file preserves existing keys"""
        state_path = tmp_path / "state.yaml"
        
        # Create initial state
        initial_data = {
            'project_id': 'PROJ-533',
            'existing_key': 'existing_value',
            'artifact_hashes': {'old_file.csv': 'old_hash'}
        }
        with open(state_path, 'w') as f:
            yaml.dump(initial_data, f)
        
        # Update with new checksums
        new_checksums = {'new_file.csv': 'new_hash'}
        update_project_state(str(state_path), new_checksums)
        
        with open(state_path, 'r') as f:
            data = yaml.safe_load(f)
        
        assert data['project_id'] == 'PROJ-533'
        assert data['existing_key'] == 'existing_value'
        assert data['artifact_hashes']['old_file.csv'] == 'old_hash'
        assert data['artifact_hashes']['new_file.csv'] == 'new_hash'
        assert 'last_updated' in data

    def test_create_directory_if_missing(self, tmp_path):
        """Test that update_project_state creates the directory if it doesn't exist"""
        nested_dir = tmp_path / "level1" / "level2"
        state_path = nested_dir / "state.yaml"
        checksums = {'test.csv': 'test_hash'}
        
        update_project_state(str(state_path), checksums)
        
        assert state_path.exists()
        assert nested_dir.exists()