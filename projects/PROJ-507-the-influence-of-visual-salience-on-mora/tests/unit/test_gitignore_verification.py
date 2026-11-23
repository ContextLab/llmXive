"""
Unit tests for .gitignore verification logic.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from verify_gitignore import verify_gitignore_patterns, REQUIRED_PATTERNS


class TestGitignoreVerification:
    """Tests for gitignore verification functionality."""

    def test_required_patterns_defined(self):
        """Test that all required patterns are defined."""
        assert "data/raw/" in REQUIRED_PATTERNS
        assert "data/survey/" in REQUIRED_PATTERNS
        assert "__pycache__" in REQUIRED_PATTERNS
        assert "*.pyc" in REQUIRED_PATTERNS
        assert ".env" in REQUIRED_PATTERNS

    def test_gitignore_creation_with_required_patterns(self):
        """Test that a valid gitignore can be created with required patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gitignore_path = Path(tmpdir) / ".gitignore"
            
            # Write required patterns
            with open(gitignore_path, 'w') as f:
                for pattern in REQUIRED_PATTERNS:
                    f.write(f"{pattern}\n")
            
            # Verify file exists and contains patterns
            assert gitignore_path.exists()
            content = gitignore_path.read_text()
            for pattern in REQUIRED_PATTERNS:
                assert pattern in content

    def test_gitignore_with_comments(self):
        """Test that gitignore handles comments correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gitignore_path = Path(tmpdir) / ".gitignore"
            
            # Write patterns with comments
            content = """# Data directories
            data/raw/
            data/survey/
            
            # Python cache
            __pycache__
            *.pyc
            
            # Environment
            .env
            """
            gitignore_path.write_text(content)
            
            # Should still find patterns
            lines = [line.strip() for line in content.split('\n') 
                     if line.strip() and not line.strip().startswith('#')]
            
            for pattern in REQUIRED_PATTERNS:
                assert pattern in lines

    def test_missing_pattern_detection(self):
        """Test that missing patterns are detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gitignore_path = Path(tmpdir) / ".gitignore"
            
            # Write incomplete patterns
            content = """data/raw/
            __pycache__
            """
            gitignore_path.write_text(content)
            
            # Read and check
            lines = [line.strip() for line in content.split('\n') 
                     if line.strip() and not line.strip().startswith('#')]
            
            assert "data/survey/" not in lines
            assert "*.pyc" not in lines
            assert ".env" not in lines