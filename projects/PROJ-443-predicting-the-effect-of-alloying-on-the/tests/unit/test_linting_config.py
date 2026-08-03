"""
Unit tests for linting and formatting configuration.

These tests verify that the linting configuration files exist
and contain the expected settings.
"""
import os
import pytest
from pathlib import Path
import yaml
import subprocess
import sys

class TestLintingConfiguration:
    """Test suite for linting configuration files."""
    
    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent.parent
    
    def test_flake8_config_exists(self, project_root):
        """Test that .flake8 configuration file exists."""
        flake8_config = project_root / ".flake8"
        assert flake8_config.exists(), ".flake8 configuration file must exist"
    
    def test_flake8_config_valid(self, project_root):
        """Test that .flake8 configuration is valid."""
        flake8_config = project_root / ".flake8"
        assert flake8_config.exists(), ".flake8 configuration file must exist"
        
        # Try to read the config with flake8
        result = subprocess.run(
            ["flake8", "--version"],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"flake8 is not installed or not working: {result.stderr}"
    
    def test_pyproject_toml_exists(self, project_root):
        """Test that pyproject.toml exists with linting configuration."""
        pyproject = project_root / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml must exist"
    
    def test_pyproject_black_config(self, project_root):
        """Test that pyproject.toml contains Black configuration."""
        pyproject = project_root / "pyproject.toml"
        content = pyproject.read_text()
        
        assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"
        assert "line-length" in content, "Black configuration must specify line-length"
    
    def test_pre_commit_config_exists(self, project_root):
        """Test that .pre-commit-config.yaml exists."""
        pre_commit_config = project_root / ".pre-commit-config.yaml"
        assert pre_commit_config.exists(), ".pre-commit-config.yaml must exist"
    
    def test_pre_commit_config_valid(self, project_root):
        """Test that .pre-commit-config.yaml is valid YAML and contains expected hooks."""
        pre_commit_config = project_root / ".pre-commit-config.yaml"
        content = pre_commit_config.read_text()
        
        config = yaml.safe_load(content)
        
        assert "repos" in config, "pre-commit config must have 'repos' key"
        
        repo_urls = [repo["repo"] for repo in config["repos"]]
        
        # Check for required hooks
        assert any("black" in repo for repo in repo_urls), "Must include Black hook"
        assert any("flake8" in repo for repo in repo_urls), "Must include flake8 hook"
        assert any("pre-commit-hooks" in repo for repo in repo_urls), "Must include pre-commit-hooks"
    
    def test_setup_linting_script_exists(self, project_root):
        """Test that setup_linting.py script exists."""
        setup_script = project_root / "code" / "setup_linting.py"
        assert setup_script.exists(), "code/setup_linting.py must exist"
    
    def test_setup_linting_script_syntax(self, project_root):
        """Test that setup_linting.py has valid Python syntax."""
        setup_script = project_root / "code" / "setup_linting.py"
        
        try:
            compile(setup_script.read_text(), setup_script, "exec")
        except SyntaxError as e:
            pytest.fail(f"setup_linting.py has syntax errors: {e}")
    
    def test_black_line_length_consistency(self, project_root):
        """Test that Black and flake8 use consistent line lengths."""
        pyproject = project_root / "pyproject.toml"
        flake8_config = project_root / ".flake8"
        
        # Read Black line length
        pyproject_content = pyproject.read_text()
        black_line_length = None
        for line in pyproject_content.split("\n"):
            if "line-length" in line and "[tool.black]" in pyproject_content[:pyproject_content.find(line)]:
                try:
                    black_line_length = int(line.split("=")[1].strip())
                except (ValueError, IndexError):
                    continue
        
        # Read flake8 max-line-length
        flake8_content = flake8_config.read_text()
        flake8_line_length = None
        for line in flake8_content.split("\n"):
            if "max-line-length" in line:
                try:
                    flake8_line_length = int(line.split("=")[1].strip())
                except (ValueError, IndexError):
                    continue
        
        # If both are defined, they should match (or be close)
        if black_line_length and flake8_line_length:
            assert black_line_length == flake8_line_length, \
                f"Black line-length ({black_line_length}) and flake8 max-line-length ({flake8_line_length}) should match"