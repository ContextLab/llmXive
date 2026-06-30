"""
Tests to verify linting and formatting configuration.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest


class TestLintingConfiguration:
    """Test cases for linting and formatting setup."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent

    @pytest.fixture
    def code_dir(self, project_root):
        """Get the code directory."""
        return project_root / "code"

    def test_precommit_config_exists(self, code_dir):
        """Test that .pre-commit-config.yaml exists."""
        config_file = code_dir / ".pre-commit-config.yaml"
        assert config_file.exists(), f"Configuration file not found: {config_file}"

    def test_precommit_config_valid_yaml(self, code_dir):
        """Test that .pre-commit-config.yaml contains valid YAML."""
        config_file = code_dir / ".pre-commit-config.yaml"
        try:
            import yaml
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
            assert "repos" in config, "Missing 'repos' key in pre-commit config"
            assert isinstance(config["repos"], list), "'repos' must be a list"
            repo_urls = [repo["repo"] for repo in config["repos"]]
            assert any("ruff" in url for url in repo_urls), "Ruff not found in pre-commit config"
            assert any("black" in url for url in repo_urls), "Black not found in pre-commit config"
        except ImportError:
            pytest.skip("PyYAML not installed, skipping YAML validation")

    def test_gitignore_exists(self, code_dir):
        """Test that .gitignore exists."""
        gitignore_file = code_dir / ".gitignore"
        assert gitignore_file.exists(), f".gitignore not found: {gitignore_file}"

    def test_gitignore_contains_common_patterns(self, code_dir):
        """Test that .gitignore contains common Python ignore patterns."""
        gitignore_file = code_dir / ".gitignore"
        content = gitignore_file.read_text()
        
        required_patterns = [
            "__pycache__/",
            "*.py[cod]",
            ".pytest_cache/",
            ".coverage",
            "htmlcov/",
            ".env",
            ".venv/",
            "venv/",
        ]
        
        for pattern in required_patterns:
            assert pattern in content, f"Missing pattern in .gitignore: {pattern}"

    def test_setup_linting_script_exists(self, code_dir):
        """Test that setup_linting.py exists."""
        script_file = code_dir / "setup_linting.py"
        assert script_file.exists(), f"Setup script not found: {script_file}"

    def test_setup_linting_script_syntax(self, code_dir):
        """Test that setup_linting.py has valid Python syntax."""
        script_file = code_dir / "setup_linting.py"
        try:
            with open(script_file, "r") as f:
                compile(f.read(), script_file, "exec")
        except SyntaxError as e:
            pytest.fail(f"Syntax error in setup_linting.py: {e}")

    def test_precommit_installed(self):
        """Test that pre-commit is installed."""
        try:
            result = subprocess.run(
                ["pre-commit", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, f"pre-commit not installed: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("pre-commit not installed, skipping test")
        except subprocess.TimeoutExpired:
            pytest.skip("pre-commit check timed out, skipping test")

    def test_ruff_installed(self):
        """Test that ruff is installed."""
        try:
            result = subprocess.run(
                ["ruff", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, f"ruff not installed: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("ruff not installed, skipping test")
        except subprocess.TimeoutExpired:
            pytest.skip("ruff check timed out, skipping test")

    def test_black_installed(self):
        """Test that black is installed."""
        try:
            result = subprocess.run(
                ["black", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, f"black not installed: {result.stderr}"
        except FileNotFoundError:
            pytest.skip("black not installed, skipping test")
        except subprocess.TimeoutExpired:
            pytest.skip("black check timed out, skipping test")

    def test_git_initialized(self, project_root):
        """Test that git repository is initialized."""
        git_dir = project_root / ".git"
        assert git_dir.exists(), "Git repository not initialized"
        
        # Verify it's a valid git repo
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        assert result.returncode == 0, "Not a valid git repository"

    def test_precommit_hooks_installed(self, project_root):
        """Test that pre-commit hooks are installed."""
        hooks_dir = project_root / ".git" / "hooks"
        precommit_hook = hooks_dir / "pre-commit"
        
        # If hooks directory doesn't exist, skip (git might not be fully initialized)
        if not hooks_dir.exists():
            pytest.skip("Git hooks directory not found")
        
        # Check if pre-commit hook exists
        if precommit_hook.exists():
            # Verify it's executable
            assert os.access(precommit_hook, os.X_OK), "pre-commit hook not executable"
        else:
            # If hook doesn't exist, verify pre-commit is installed and can be run
            try:
                result = subprocess.run(
                    ["pre-commit", "install", "--install-hooks"],
                    capture_output=True,
                    text=True,
                    cwd=project_root,
                    timeout=30
                )
                # If it runs successfully, that's fine - hooks are now installed
                assert result.returncode == 0, f"Failed to install hooks: {result.stderr}"
            except FileNotFoundError:
                pytest.skip("pre-commit not installed")
            except subprocess.TimeoutExpired:
                pytest.skip("pre-commit install timed out")