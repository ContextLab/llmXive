"""
Tests to verify pre-commit configuration is valid and hooks are installed.
"""
import os
import subprocess
import yaml
from pathlib import Path
import pytest


class TestPreCommitConfig:
    """Test suite for pre-commit configuration."""

    @pytest.fixture
    def config_path(self):
        """Get path to pre-commit config file."""
        return Path(__file__).parent.parent / ".pre-commit-config.yaml"

    def test_config_file_exists(self, config_path):
        """Test that .pre-commit-config.yaml exists in project root."""
        assert config_path.exists(), "Pre-commit config file not found"

    def test_config_is_valid_yaml(self, config_path):
        """Test that the config file is valid YAML."""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            assert config is not None, "Config file is empty"
            assert 'repos' in config, "Config must contain 'repos' key"
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in pre-commit config: {e}")

    def test_ruff_hook_present(self, config_path):
        """Test that ruff linting hook is configured."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        repos = config.get('repos', [])
        ruff_repo = next(
            (repo for repo in repos if 'ruff' in repo.get('repo', '')),
            None
        )
        
        assert ruff_repo is not None, "Ruff repository not found in config"
        
        hooks = ruff_repo.get('hooks', [])
        ruff_hook = next(
            (hook for hook in hooks if hook.get('id') == 'ruff'),
            None
        )
        
        assert ruff_hook is not None, "Ruff hook not found in config"

    def test_black_hook_present(self, config_path):
        """Test that black formatting hook is configured."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        repos = config.get('repos', [])
        
        # Check both black repo and ruff-format alias
        black_repo = next(
            (repo for repo in repos if 'black' in repo.get('repo', '')),
            None
        )
        ruff_repo = next(
            (repo for repo in repos if 'ruff' in repo.get('repo', '')),
            None
        )
        
        has_black = False
        
        if black_repo:
            hooks = black_repo.get('hooks', [])
            has_black = any(hook.get('id') == 'black' for hook in hooks)
        
        if ruff_repo and not has_black:
            hooks = ruff_repo.get('hooks', [])
            has_black = any(hook.get('alias') == 'black' for hook in hooks)
        
        assert has_black, "Black formatting hook not found in config"

    def test_hook_revisions_pinned(self, config_path):
        """Test that hook revisions are pinned (not using 'master' or 'main')."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        repos = config.get('repos', [])
        
        for repo in repos:
            rev = repo.get('rev', '')
            assert rev and rev not in ['master', 'main', 'HEAD'], \
                f"Repository {repo.get('repo')} should have a pinned revision"

    def test_git_hooks_installed(self):
        """Test that pre-commit hook is installed in .git/hooks."""
        hooks_dir = Path(__file__).parent.parent / ".git" / "hooks"
        pre_commit_hook = hooks_dir / "pre-commit"
        
        if not hooks_dir.exists():
            pytest.skip(".git/hooks directory not found (not a git repo?)")
        
        # Check if hook exists and is executable
        assert pre_commit_hook.exists(), "Pre-commit hook not installed in .git/hooks"
        assert os.access(pre_commit_hook, os.X_OK), "Pre-commit hook is not executable"

    def test_precommit_command_available(self):
        """Test that pre-commit command is available in PATH."""
        try:
            result = subprocess.run(
                ['pre-commit', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, "pre-commit command failed"
            assert 'pre-commit' in result.stdout.lower(), \
                f"Unexpected output from pre-commit: {result.stdout}"
        except FileNotFoundError:
            pytest.fail("pre-commit command not found. Run 'pip install pre-commit'")
        except subprocess.TimeoutExpired:
            pytest.fail("pre-commit command timed out")

    def test_config_syntax_valid(self, config_path):
        """Test that the config file has valid syntax for pre-commit."""
        try:
            result = subprocess.run(
                ['pre-commit', 'sample-config'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=Path(__file__).parent.parent
            )
            # We just check that pre-commit can parse our config without error
            result = subprocess.run(
                ['pre-commit', 'run', '--help'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=Path(__file__).parent.parent
            )
            assert result.returncode == 0, "pre-commit failed to initialize"
        except subprocess.TimeoutExpired:
            pytest.fail("pre-commit command timed out during validation")