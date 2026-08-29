"""
Unit tests for setup_linting.py functionality.
"""

import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
# Adjust import path based on how tests are run
try:
    from code.setup_linting import create_pyproject_config, create_gitignore_entries
except ImportError:
    # Fallback for different execution contexts
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from code.setup_linting import create_pyproject_config, create_gitignore_entries


class TestCreatePyprojectConfig:
    def test_creates_file_when_not_exists(self):
        """Test that pyproject.toml is created with correct configuration."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            pyproject_path = root / "pyproject.toml"
            
            create_pyproject_config(root)
            
            assert pyproject_path.exists()
            content = pyproject_path.read_text()
            
            assert "[tool.black]" in content
            assert "[tool.ruff]" in content
            assert "line-length = 88" in content
            assert "target-version" in content

    def test_appends_when_exists_without_config(self):
        """Test that configuration is appended to existing pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            pyproject_path = root / "pyproject.toml"
            
            # Create empty pyproject.toml
            pyproject_path.write_text("[project]\nname = \"test\"")
            
            create_pyproject_config(root)
            
            content = pyproject_path.read_text()
            assert "[project]" in content
            assert "[tool.black]" in content
            assert "[tool.ruff]" in content

    def test_skips_when_already_configured(self):
        """Test that configuration is not duplicated if already present."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            pyproject_path = root / "pyproject.toml"
            
            # Create pyproject.toml with existing config
            initial_content = "[tool.black]\nline-length = 88"
            pyproject_path.write_text(initial_content)
            
            create_pyproject_config(root)
            
            content = pyproject_path.read_text()
            # Should not have doubled the black section
            assert content.count("[tool.black]") == 1


class TestCreateGitignoreEntries:
    def test_creates_file_when_not_exists(self):
        """Test that .gitignore is created with linting entries."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gitignore_path = root / ".gitignore"
            
            create_gitignore_entries(root)
            
            assert gitignore_path.exists()
            content = gitignore_path.read_text()
            
            assert ".ruff_cache/" in content
            assert ".black_cache/" in content

    def test_appends_when_exists_without_entries(self):
        """Test that entries are appended to existing .gitignore."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gitignore_path = root / ".gitignore"
            
            gitignore_path.write_text("# Existing ignore\n__pycache__/\n")
            
            create_gitignore_entries(root)
            
            content = gitignore_path.read_text()
            assert "__pycache__/" in content
            assert ".ruff_cache/" in content

    def test_skips_when_already_present(self):
        """Test that entries are not duplicated if already present."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            gitignore_path = root / ".gitignore"
            
            initial_content = "# Linting\n.ruff_cache/\n"
            gitignore_path.write_text(initial_content)
            
            create_gitignore_entries(root)
            
            content = gitignore_path.read_text()
            # Should not have doubled the entry
            assert content.count(".ruff_cache/") == 1