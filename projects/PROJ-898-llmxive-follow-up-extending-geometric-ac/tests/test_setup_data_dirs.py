import os
import tempfile
import pytest
from code.setup_data_dirs import ensure_gitkeep


class TestEnsureGitkeep:
    def test_creates_directory_and_gitkeep(self, tmp_path):
        """Test that ensure_gitkeep creates the directory and .gitkeep file."""
        test_dir = os.path.join(str(tmp_path), "test_subdir")
        ensure_gitkeep(test_dir)
        
        assert os.path.isdir(test_dir)
        gitkeep_path = os.path.join(test_dir, ".gitkeep")
        assert os.path.isfile(gitkeep_path)
        
        with open(gitkeep_path, "r") as f:
            content = f.read()
        assert "Keep this directory in git" in content

    def test_does_not_overwrite_existing_gitkeep(self, tmp_path):
        """Test that ensure_gitkeep does not overwrite an existing .gitkeep."""
        test_dir = os.path.join(str(tmp_path), "test_subdir")
        os.makedirs(test_dir, exist_ok=True)
        
        original_content = "original content"
        gitkeep_path = os.path.join(test_dir, ".gitkeep")
        with open(gitkeep_path, "w") as f:
            f.write(original_content)
        
        ensure_gitkeep(test_dir)
        
        with open(gitkeep_path, "r") as f:
            content = f.read()
        assert content == original_content

    def test_handles_nested_directories(self, tmp_path):
        """Test that ensure_gitkeep handles nested directory paths."""
        test_dir = os.path.join(str(tmp_path), "level1", "level2")
        ensure_gitkeep(test_dir)
        
        assert os.path.isdir(test_dir)
        gitkeep_path = os.path.join(test_dir, ".gitkeep")
        assert os.path.isfile(gitkeep_path)
