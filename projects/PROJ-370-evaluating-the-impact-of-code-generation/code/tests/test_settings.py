import pytest
import json
from pathlib import Path
from unittest.mock import patch
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.config.settings import get_config, get_target_repos, get_paths, ensure_directories, DEFAULT_CONFIG

class TestSettings:
    """Test suite for configuration management."""

    def test_get_config_returns_dict(self):
        """Test that get_config returns a dictionary."""
        config = get_config()
        assert isinstance(config, dict)
        assert "random_seed" in config
        assert "target_repos" in config

    def test_get_config_has_defaults(self):
        """Test that default configuration values are present."""
        config = get_config()
        assert config["random_seed"] == 42
        assert config["max_runtime_hours"] == 6
        assert config["similarity_threshold"] == 0.85

    def test_get_target_repos_returns_list(self):
        """Test that get_target_repos returns a list of strings."""
        repos = get_target_repos()
        assert isinstance(repos, list)
        assert len(repos) >= 3
        for repo in repos:
            assert isinstance(repo, str)
            assert "/" in repo  # owner/repo format

    def test_get_target_repos_validation(self):
        """Test that get_target_repos validates the repository list."""
        # Test with valid repos (should not raise)
        with patch("code.config.settings._config", {"target_repos": ["owner/repo1", "owner/repo2", "owner/repo3"]}):
            repos = get_target_repos()
            assert len(repos) == 3

        # Test with invalid format
        with patch("code.config.settings._config", {"target_repos": ["invalid_repo"]}):
            with pytest.raises(ValueError, match="Invalid repository format"):
                get_target_repos()

        # Test with insufficient repos
        with patch("code.config.settings._config", {"target_repos": ["owner/repo"]}):
            with pytest.raises(ValueError, match="expected at least 3 repositories"):
                get_target_repos()

    def test_get_paths_returns_correct_structure(self):
        """Test that get_paths returns all required directories."""
        paths = get_paths()
        required_keys = [
            "src", "data", "data_raw", "data_derived", 
            "data_annotations", "results", "tests", "specs",
            "contracts", "logs", "state", "figures"
        ]
        for key in required_keys:
            assert key in paths
            assert isinstance(paths[key], Path)

    def test_paths_are_absolute(self):
        """Test that all returned paths are absolute."""
        paths = get_paths()
        for path in paths.values():
            assert path.is_absolute()

    def test_ensure_directories_creates_folders(self):
        """Test that ensure_directories creates the required folder structure."""
        # Get paths
        paths = get_paths()
        
        # Remove existing directories (if any)
        for path in paths.values():
            if path.exists():
                import shutil
                shutil.rmtree(path)
        
        # Create directories
        ensure_directories()
        
        # Verify they exist
        for path in paths.values():
            assert path.exists(), f"Directory {path} was not created"
            assert path.is_dir(), f"Path {path} is not a directory"

    def test_config_merge_with_file(self, tmp_path):
        """Test that config file overrides defaults."""
        # Create a temporary config file
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "settings.json"
        
        custom_config = {
            "random_seed": 123,
            "target_repos": ["custom/repo1", "custom/repo2", "custom/repo3"]
        }
        
        with open(config_file, "w") as f:
            json.dump(custom_config, f)
        
        # Mock PROJECT_ROOT to point to tmp_path
        with patch("code.config.settings.PROJECT_ROOT", tmp_path):
            # Clear cache
            import code.config.settings as settings_module
            settings_module._config = {}
            
            config = settings_module.get_config()
            
            assert config["random_seed"] == 123
            assert config["target_repos"] == ["custom/repo1", "custom/repo2", "custom/repo3"]
            # Default values should still be present
            assert "max_runtime_hours" in config