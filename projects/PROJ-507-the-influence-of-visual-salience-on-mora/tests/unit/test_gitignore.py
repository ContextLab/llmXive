"""
Unit tests for .gitignore verification.
"""
import os
import tempfile
from pathlib import Path
import pytest

# Import the verification logic
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from verify_gitignore import verify_gitignore_patterns, check_git_ignore_effectiveness

class TestGitignoreVerification:
    """Test cases for .gitignore verification functions."""

    def test_verify_gitignore_patterns_missing_file(self):
        """Test that verification fails when .gitignore is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            gitignore_path = project_root / '.gitignore'
            
            result = verify_gitignore_patterns(gitignore_path, project_root)
            assert result is False

    def test_verify_gitignore_patterns_complete(self):
        """Test that verification passes when all patterns are present."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            gitignore_path = project_root / '.gitignore'
            
            # Write a complete .gitignore
            content = """
            data/raw/
            data/survey/
            __pycache__/
            *.pyc
            .env
            """
            gitignore_path.write_text(content)
            
            result = verify_gitignore_patterns(gitignore_path, project_root)
            assert result is True

    def test_verify_gitignore_patterns_missing_one(self):
        """Test that verification fails when one pattern is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            gitignore_path = project_root / '.gitignore'
            
            # Write a .gitignore missing one pattern
            content = """
            data/raw/
            __pycache__/
            *.pyc
            .env
            """
            gitignore_path.write_text(content)
            
            result = verify_gitignore_patterns(gitignore_path, project_root)
            assert result is False

    def test_check_git_ignore_effectiveness_no_git(self):
        """Test that effectiveness check passes when git is not available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            # Don't initialize git repo
            
            result = check_git_ignore_effectiveness(project_root)
            # Should return True because git is not initialized
            assert result is True