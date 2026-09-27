"""
Unit tests to verify Git repository initialization artifacts.
These tests check for the existence of .git, .gitignore, and commit history.
"""
import os
import subprocess
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent / "projects" / "PROJ-846-llmxive-follow-up-extending-guava-an-eff"

def test_gitignore_exists():
    """Verify .gitignore file exists in the project root."""
    gitignore_path = PROJECT_ROOT / ".gitignore"
    assert gitignore_path.exists(), f".gitignore not found at {gitignore_path}"
    
    content = gitignore_path.read_text()
    assert "*.pyc" in content, "Missing *.pyc in .gitignore"
    assert "__pycache__" in content, "Missing __pycache__ in .gitignore"
    assert ".env" in content, "Missing .env in .gitignore"
    assert "data/raw/*" in content, "Missing data/raw/* in .gitignore"
    assert "data/artifacts/*" in content, "Missing data/artifacts/* in .gitignore"
    assert "*.log" in content, "Missing *.log in .gitignore"
    assert "*.pth" in content, "Missing *.pth in .gitignore"

def test_git_directory_exists():
    """Verify .git directory exists in the project root."""
    git_dir = PROJECT_ROOT / ".git"
    assert git_dir.exists(), f".git directory not found at {git_dir}"
    assert git_dir.is_dir(), f"{git_dir} is not a directory"

def test_commit_history_exists():
    """Verify that there is at least one commit in the history."""
    if not (PROJECT_ROOT / ".git").exists():
        pytest.skip("Git repository not initialized, skipping commit history check.")
    
    try:
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True
        )
        lines = result.stdout.strip().split('\n')
        assert len(lines) >= 1, "No commits found in git history"
        assert "Initial commit" in lines[0], f"First commit message does not contain 'Initial commit': {lines[0]}"
    except subprocess.CalledProcessError:
        pytest.fail("Could not retrieve git log.")