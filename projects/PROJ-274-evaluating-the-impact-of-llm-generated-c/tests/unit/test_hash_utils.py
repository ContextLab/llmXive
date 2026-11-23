import os
import tempfile
import json
import yaml
from pathlib import Path
import pytest

# Import the functions we are testing
# We assume the code is in code/utils/hash_utils.py
# We need to add the parent directory to sys.path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.hash_utils import calculate_directory_hash, update_project_state

class TestHashUtils:
    
    def test_calculate_directory_hash_empty_dir(self, tmp_path):
        """Test hashing an empty directory."""
        # Create a temp directory with no files
        test_dir = tmp_path / "empty_dir"
        test_dir.mkdir()
        
        # Calculate hash
        hash_val = calculate_directory_hash(str(test_dir))
        
        # Verify hash is a valid hex string of correct length (SHA256)
        assert len(hash_val) == 64
        assert all(c in '0123456789abcdef' for c in hash_val)
    
    def test_calculate_directory_hash_with_file(self, tmp_path):
        """Test hashing a directory with a single file."""
        test_dir = tmp_path / "file_dir"
        test_dir.mkdir()
        
        # Create a file with known content
        test_file = test_dir / "test.txt"
        test_file.write_text("Hello World")
        
        # Calculate hash
        hash_val = calculate_directory_hash(str(test_dir))
        
        # Verify hash is valid
        assert len(hash_val) == 64
        
        # Verify determinism: calculate again and ensure same hash
        hash_val_2 = calculate_directory_hash(str(test_dir))
        assert hash_val == hash_val_2
    
    def test_calculate_directory_hash_different_content(self, tmp_path):
        """Test that different content produces different hashes."""
        test_dir_1 = tmp_path / "dir1"
        test_dir_1.mkdir()
        (test_dir_1 / "file.txt").write_text("Content A")
        
        test_dir_2 = tmp_path / "dir2"
        test_dir_2.mkdir()
        (test_dir_2 / "file.txt").write_text("Content B")
        
        hash_1 = calculate_directory_hash(str(test_dir_1))
        hash_2 = calculate_directory_hash(str(test_dir_2))
        
        assert hash_1 != hash_2
    
    def test_update_project_state_creates_file(self, tmp_path):
        """Test that update_project_state creates the state file."""
        project_root = tmp_path
        project_id = "TEST-PROJ-001"
        test_hash = "a" * 64
        
        update_project_state(str(project_root), project_id, test_hash, 'state')
        
        state_file = project_root / 'state' / f"{project_id}.yaml"
        assert state_file.exists()
        
        # Verify content
        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)
        
        assert 'projects' in data
        assert project_id in data['projects']
        assert data['projects'][project_id]['initial_hash'] == test_hash
    
    def test_update_project_state_updates_existing(self, tmp_path):
        """Test updating an existing state file."""
        project_root = tmp_path
        project_id = "TEST-PROJ-002"
        
        # First update
        hash_1 = "b" * 64
        update_project_state(str(project_root), project_id, hash_1, 'state')
        
        # Second update
        hash_2 = "c" * 64
        update_project_state(str(project_root), project_id, hash_2, 'state')
        
        state_file = project_root / 'state' / f"{project_id}.yaml"
        with open(state_file, 'r') as f:
            data = yaml.safe_load(f)
        
        # Should reflect the latest hash
        assert data['projects'][project_id]['initial_hash'] == hash_2
    
    def test_non_existent_directory_raises(self, tmp_path):
        """Test that calculating hash on non-existent dir raises error."""
        fake_path = tmp_path / "non_existent"
        
        with pytest.raises(FileNotFoundError):
            calculate_directory_hash(str(fake_path))