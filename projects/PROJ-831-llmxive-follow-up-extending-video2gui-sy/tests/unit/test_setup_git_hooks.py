"""
Unit tests for git hooks setup and content generation.
"""
import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from setup_git_hooks import (
    create_precommit_hook,
    setup_git_hooks,
    PII_PATTERNS,
    SCHEMA_FILES,
)


class TestCreatePrecommitHook:
    def test_hook_content_exists(self):
        """Test that hook content is generated."""
        content = create_precommit_hook()
        assert isinstance(content, str)
        assert len(content) > 0

    def test_hook_includes_schema_check(self):
        """Test that hook content includes schema validation logic."""
        content = create_precommit_hook()
        assert "Schema validation" in content
        for schema in SCHEMA_FILES:
            assert schema in content

    def test_hook_includes_pii_scan(self):
        """Test that hook content includes PII scanning logic."""
        content = create_precommit_hook()
        assert "PII scan" in content
        # Check if a sample pattern is included (escaped)
        assert "SSN" in content or r"\d{3}-\d{2}-\d{4}" in content

    def test_hook_is_executable_script(self):
        """Test that the generated content starts with a shebang."""
        content = create_precommit_hook()
        assert content.startswith("#!/bin/bash")


class TestSetupGitHooks:
    @pytest.fixture
    def mock_git_repo(self, tmp_path):
        """Create a mock git repository structure."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir()
        return tmp_path

    @patch("setup_git_hooks.get_project_root")
    def test_setup_creates_hook_file(self, mock_get_root, mock_git_repo):
        """Test that setup creates the pre-commit hook file."""
        mock_get_root.return_value = mock_git_repo

        setup_git_hooks()

        hook_path = mock_git_repo / ".git" / "hooks" / "pre-commit"
        assert hook_path.exists()

    @patch("setup_git_hooks.get_project_root")
    def test_setup_makes_hook_executable(self, mock_get_root, mock_git_repo):
        """Test that the hook file is made executable."""
        mock_get_root.return_value = mock_git_repo

        setup_git_hooks()

        hook_path = mock_git_repo / ".git" / "hooks" / "pre-commit"
        assert os.access(hook_path, os.X_OK)

    @patch("setup_git_hooks.get_project_root")
    def test_setup_fails_if_not_git_repo(self, mock_get_root, tmp_path):
        """Test that setup fails if .git directory is missing."""
        mock_get_root.return_value = tmp_path

        with pytest.raises(SystemExit):
            setup_git_hooks()

    @patch("setup_git_hooks.get_project_root")
    def test_hook_content_is_written_correctly(self, mock_get_root, mock_git_repo):
        """Test that the hook content is written correctly to the file."""
        mock_get_root.return_value = mock_git_repo

        setup_git_hooks()

        hook_path = mock_git_repo / ".git" / "hooks" / "pre-commit"
        with open(hook_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Schema validation" in content
        assert "PII scan" in content
        assert "exit 0" in content