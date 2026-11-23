import os
import sys
import csv
import yaml
from pathlib import Path
import pytest

# Ensure code is in path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_dirs import ensure_directory, initialize_checksums_file, initialize_state_file

class TestSetupDirs:
    @pytest.fixture
    def temp_project_root(self, tmp_path):
        """Create a temporary project root structure for testing."""
        root = tmp_path / "projects" / "PROJ-334-test"
        root.mkdir(parents=True, exist_ok=True)
        return root

    def test_ensure_directory_creates_new(self, temp_project_root):
        """Test that ensure_directory creates a new directory."""
        new_dir = temp_project_root / "new_subdir"
        assert not new_dir.exists()
        ensure_directory(str(new_dir))
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_exists(self, temp_project_root):
        """Test that ensure_directory does nothing if directory exists."""
        existing_dir = temp_project_root / "existing"
        existing_dir.mkdir(parents=True, exist_ok=True)
        ensure_directory(str(existing_dir))
        # Should not raise an error

    def test_initialize_checksums_file_creates(self, temp_project_root):
        """Test that initialize_checksums_file creates the file with header."""
        checksums_path = temp_project_root / "data" / "checksums.txt"
        initialize_checksums_file(str(checksums_path))
        
        assert checksums_path.exists()
        with open(checksums_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            assert header == ['filename', 'sha256_hash']

    def test_initialize_checksums_file_exists(self, temp_project_root):
        """Test that initialize_checksums_file does nothing if file exists."""
        checksums_path = temp_project_root / "data" / "checksums.txt"
        checksums_path.parent.mkdir(parents=True, exist_ok=True)
        checksums_path.touch()
        initialize_checksums_file(str(checksums_path))
        # Should not raise an error

    def test_initialize_state_file_creates(self, temp_project_root):
        """Test that initialize_state_file creates the YAML file with correct structure."""
        state_path = temp_project_root / "state" / "projects" / "PROJ-334-test.yaml"
        initialize_state_file(str(state_path))
        
        assert state_path.exists()
        with open(state_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            assert 'artifact_hashes' in data
            assert data['artifact_hashes'] == {}
            assert 'updated_at' in data
            assert data['updated_at'] == '1970-01-01T00:00:00Z'

    def test_initialize_state_file_exists(self, temp_project_root):
        """Test that initialize_state_file does nothing if file exists."""
        state_path = temp_project_root / "state" / "projects" / "PROJ-334-test.yaml"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.touch()
        initialize_state_file(str(state_path))
        # Should not raise an error