"""
Unit tests for configuration setup.

Tests that ruff and black configurations are correctly created.
"""
import os
import sys
import tempfile
from pathlib import Path
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup.configure_tools import create_ruff_config, create_black_config, create_mypy_config


class TestConfigCreation:
    """Test configuration file creation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.root_path = Path(self.test_dir)

    def teardown_method(self):
        """Clean up test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_ruff_config_creation(self):
        """Test that ruff configuration is created."""
        config_path = self.root_path / "pyproject.toml"
        
        # Create ruff config
        create_ruff_config(self.root_path)
        
        # Verify file exists
        assert config_path.exists(), "pyproject.toml should be created"
        
        # Verify content contains ruff config
        content = config_path.read_text()
        assert "[tool.ruff]" in content, "Ruff configuration should be in pyproject.toml"
        assert "line-length = 88" in content, "Ruff line-length should be 88"
        assert "target-version = \"py311\"" in content, "Ruff target version should be py311"

    def test_black_config_creation(self):
        """Test that black configuration is created."""
        config_path = self.root_path / "pyproject.toml"
        
        # Create black config
        create_black_config(self.root_path)
        
        # Verify file exists
        assert config_path.exists(), "pyproject.toml should be created"
        
        # Verify content contains black config
        content = config_path.read_text()
        assert "[tool.black]" in content, "Black configuration should be in pyproject.toml"
        assert "line-length = 88" in content, "Black line-length should be 88"
        assert "target-version = ['py311']" in content, "Black target version should be py311"

    def test_mypy_config_creation(self):
        """Test that mypy configuration is created."""
        config_path = self.root_path / "mypy.ini"
        
        # Create mypy config
        create_mypy_config(self.root_path)
        
        # Verify file exists
        assert config_path.exists(), "mypy.ini should be created"
        
        # Verify content
        content = config_path.read_text()
        assert "[mypy]" in content, "Mypy section should be in mypy.ini"
        assert "python_version = 3.11" in content, "Mypy python version should be 3.11"
        assert "disallow_untyped_defs = True" in content, "Mypy should disallow untyped defs"

    def test_combined_config_creation(self):
        """Test that all configs can be created together."""
        config_path = self.root_path / "pyproject.toml"
        mypy_path = self.root_path / "mypy.ini"
        
        # Create all configs
        create_ruff_config(self.root_path)
        create_black_config(self.root_path)
        create_mypy_config(self.root_path)
        
        # Verify both files exist
        assert config_path.exists(), "pyproject.toml should be created"
        assert mypy_path.exists(), "mypy.ini should be created"
        
        # Verify content
        content = config_path.read_text()
        assert "[tool.ruff]" in content, "Ruff config should be present"
        assert "[tool.black]" in content, "Black config should be present"
        
        mypy_content = mypy_path.read_text()
        assert "[mypy]" in mypy_content, "Mypy config should be present"

    def test_config_not_overwritten(self):
        """Test that existing configs are not overwritten."""
        config_path = self.root_path / "pyproject.toml"
        
        # Create initial content
        initial_content = """[project]
        name = "test"
        """
        config_path.write_text(initial_content)
        
        # Add ruff config
        create_ruff_config(self.root_path)
        content_after_ruff = config_path.read_text()
        
        # Add ruff config again
        create_ruff_config(self.root_path)
        content_after_second_ruff = config_path.read_text()
        
        # Content should be the same (not duplicated)
        assert content_after_ruff == content_after_second_ruff, "Ruff config should not be duplicated"
        
        # Add black config
        create_black_config(self.root_path)
        content_after_black = config_path.read_text()
        
        # Add black config again
        create_black_config(self.root_path)
        content_after_second_black = config_path.read_text()
        
        # Content should be the same (not duplicated)
        assert content_after_black == content_after_second_black, "Black config should not be duplicated"