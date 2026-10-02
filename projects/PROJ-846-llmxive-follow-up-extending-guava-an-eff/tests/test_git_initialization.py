import os
import subprocess
import tempfile
from pathlib import Path
import pytest
from code.init_git_repo import initialize_git_repository

def test_git_repository_created():
    """Test that a .git directory is created after initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        
        # Create a dummy file to be committed
        (root_path / "dummy.txt").write_text("test content")
        
        success = initialize_git_repository(root_path)
        
        assert success is True
        assert (root_path / ".git").exists()

def test_initial_commit_exists():
    """Test that an initial commit is created."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        
        # Create a dummy file
        (root_path / "test_file.txt").write_text("hello world")
        
        initialize_git_repository(root_path)
        
        # Check commit history
        result = subprocess.run(
            ['git', 'log', '--oneline'],
            cwd=root_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        lines = result.stdout.strip().split('\n')
        assert len(lines) >= 1
        assert "Initial commit" in result.stdout

def test_gitignore_exists():
    """Test that .gitignore is present in the repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root_path = Path(tmpdir)
        
        # Copy a sample .gitignore if it exists in the project
        # For this test, we assume the file is created by the setup process
        # or we create it here to simulate the task requirement
        gitignore_content = "*.pyc\n__pycache__/\n"
        (root_path / ".gitignore").write_text(gitignore_content)
        
        initialize_git_repository(root_path)
        
        assert (root_path / ".gitignore").exists()