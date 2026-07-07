"""
Tests for the linting and formatting configuration setup.

These tests verify that the configuration files are created correctly
and that the tools can be imported and run without errors.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the project root to the path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config_linting import (
    RUFF_CONFIG,
    BLACK_CONFIG,
    PRE_COMMIT_CONFIG,
    write_ruff_config,
    write_black_config,
    write_pre_commit_config,
    update_requirements,
    main,
)


class TestRuffConfig:
    """Tests for Ruff configuration generation"""

    def test_ruff_config_structure(self):
        """Test that Ruff configuration has expected keys"""
        assert "target-version" in RUFF_CONFIG
        assert "line-length" in RUFF_CONFIG
        assert "select" in RUFF_CONFIG
        assert "ignore" in RUFF_CONFIG
        assert "exclude" in RUFF_CONFIG
        assert "per-file-ignores" in RUFF_CONFIG

    def test_ruff_line_length(self):
        """Test that line length is set to 88 (Black compatible)"""
        assert RUFF_CONFIG["line-length"] == 88

    def test_ruff_target_version(self):
        """Test that target version is set to Python 3.10"""
        assert RUFF_CONFIG["target-version"] == "py310"

    def test_ruff_selected_rules(self):
        """Test that essential linting rules are selected"""
        essential_rules = ["E", "W", "F", "I", "B", "C4", "UP"]
        for rule in essential_rules:
            assert rule in RUFF_CONFIG["select"]

    def test_ruff_exclude_directories(self):
        """Test that data directory is excluded"""
        assert "data" in RUFF_CONFIG["exclude"]
        assert ".git" in RUFF_CONFIG["exclude"]

    def test_ruff_per_file_ignores(self):
        """Test that __init__.py has F401 ignored"""
        assert "__init__.py" in RUFF_CONFIG["per-file-ignores"]
        assert "F401" in RUFF_CONFIG["per-file-ignores"]["__init__.py"]

class TestBlackConfig:
    """Tests for Black configuration generation"""

    def test_black_config_structure(self):
        """Test that Black configuration has expected keys"""
        assert "line-length" in BLACK_CONFIG
        assert "target-version" in BLACK_CONFIG
        assert "include" in BLACK_CONFIG
        assert "exclude" in BLACK_CONFIG

    def test_black_line_length(self):
        """Test that line length is set to 88"""
        assert BLACK_CONFIG["line-length"] == 88

    def test_black_target_version(self):
        """Test that target version includes Python 3.10"""
        assert "py310" in BLACK_CONFIG["target-version"]

    def test_black_exclude_directories(self):
        """Test that data directory is excluded"""
        assert "data" in BLACK_CONFIG["exclude"]
        assert ".git" in BLACK_CONFIG["exclude"]

class TestPreCommitConfig:
    """Tests for pre-commit configuration generation"""

    def test_pre_commit_repos(self):
        """Test that Black and Ruff are in pre-commit repos"""
        repo_urls = [repo["repo"] for repo in PRE_COMMIT_CONFIG["repos"]]
        assert any("black" in url for url in repo_urls)
        assert any("ruff" in url for url in repo_urls)

    def test_pre_commit_black_hook(self):
        """Test that Black hook is configured correctly"""
        for repo in PRE_COMMIT_CONFIG["repos"]:
            if "black" in repo["repo"]:
                assert len(repo["hooks"]) == 1
                assert repo["hooks"][0]["id"] == "black"
                return
        pytest.fail("Black hook not found in pre-commit configuration")

    def test_pre_commit_ruff_hook(self):
        """Test that Ruff hook is configured correctly"""
        for repo in PRE_COMMIT_CONFIG["repos"]:
            if "ruff" in repo["repo"]:
                assert len(repo["hooks"]) == 1
                assert repo["hooks"][0]["id"] == "ruff"
                return
        pytest.fail("Ruff hook not found in pre-commit configuration")

class TestConfigFilesGeneration:
    """Tests for actual file generation"""

    def test_ruff_config_file_creation(self, tmp_path):
        """Test that Ruff config file is created"""
        # Temporarily change PROJECT_ROOT
        original_root = PROJECT_ROOT
        try:
            import code.config_linting as config_module
            config_module.PROJECT_ROOT = tmp_path
            
            result = write_ruff_config()
            assert result is True
            assert (tmp_path / ".ruff.toml").exists()
        finally:
            config_module.PROJECT_ROOT = original_root

    def test_black_config_file_creation(self, tmp_path):
        """Test that Black config is added to pyproject.toml"""
        original_root = PROJECT_ROOT
        try:
            import code.config_linting as config_module
            config_module.PROJECT_ROOT = tmp_path
            
            # Create empty pyproject.toml
            (tmp_path / "pyproject.toml").touch()
            
            result = write_black_config()
            assert result is True
            
            pyproject_content = (tmp_path / "pyproject.toml").read_text()
            assert "[tool.black]" in pyproject_content
        finally:
            config_module.PROJECT_ROOT = original_root

    def test_pre_commit_config_file_creation(self, tmp_path):
        """Test that pre-commit config file is created"""
        original_root = PROJECT_ROOT
        try:
            import code.config_linting as config_module
            config_module.PROJECT_ROOT = tmp_path
            
            result = write_pre_commit_config()
            assert result is True
            assert (tmp_path / ".pre-commit-config.yaml").exists()
        finally:
            config_module.PROJECT_ROOT = original_root

class TestRequirementsUpdate:
    """Tests for requirements.txt update"""

    def test_requirements_update(self, tmp_path):
        """Test that requirements.txt is updated with linting tools"""
        requirements_path = tmp_path / "requirements.txt"
        requirements_path.write_text("pandas\nnumpy\n")
        
        original_root = PROJECT_ROOT
        try:
            import code.config_linting as config_module
            config_module.PROJECT_ROOT = tmp_path
            
            result = update_requirements()
            assert result is True
            
            requirements_content = requirements_path.read_text()
            assert "ruff" in requirements_content
            assert "pre-commit" in requirements_content
        finally:
            config_module.PROJECT_ROOT = original_root

class TestMainFunction:
    """Tests for the main configuration function"""

    def test_main_function_success(self, tmp_path, capsys):
        """Test that main function runs successfully"""
        original_root = PROJECT_ROOT
        original_argv = sys.argv
        
        try:
            import code.config_linting as config_module
            config_module.PROJECT_ROOT = tmp_path
            sys.argv = ["config_linting.py"]
            
            # Create necessary files
            (tmp_path / "requirements.txt").write_text("pandas\nnumpy\n")
            (tmp_path / "pyproject.toml").touch()
            
            exit_code = config_module.main()
            
            assert exit_code == 0
            captured = capsys.readouterr()
            assert "Configuration complete" in captured.out
        finally:
            config_module.PROJECT_ROOT = original_root
            sys.argv = original_argv

    def test_main_function_with_missing_requirements(self, tmp_path, capsys):
        """Test that main function handles missing requirements.txt gracefully"""
        original_root = PROJECT_ROOT
        original_argv = sys.argv
        
        try:
            import code.config_linting as config_module
            config_module.PROJECT_ROOT = tmp_path
            sys.argv = ["config_linting.py"]
            
            # Don't create requirements.txt
            (tmp_path / "pyproject.toml").touch()
            
            exit_code = config_module.main()
            
            # Should still succeed (just warn about missing requirements)
            assert exit_code == 0
        finally:
            config_module.PROJECT_ROOT = original_root
            sys.argv = original_argv

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
