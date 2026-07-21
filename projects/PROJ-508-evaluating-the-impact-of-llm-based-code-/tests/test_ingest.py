"""
Tests for the data ingestion module (code/ingest.py).
"""
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ingest import calculate_llm_adoption_flag


def test_llm_adoption_cursorrules(tmp_path):
    """Test detection of .cursorrules file."""
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()
    (repo_path / ".cursorrules").touch()

    # Mock file content
    with patch("ingest.Path.read_text", return_value=""):
        flag = calculate_llm_adoption_flag(str(repo_path), [], [])
        assert flag is True


def test_llm_adoption_commit_frequency():
    """Test detection of high Copilot frequency in commits."""
    # 10 commits, 6 contain "Copilot" (60% > 5% threshold)
    commits = [
        {"commit": {"message": f"Copilot suggestion {i}"}} if i < 6
        else {"commit": {"message": f"Normal commit {i}"}}
        for i in range(10)
    ]

    flag = calculate_llm_adoption_flag("", commits, [])
    assert flag is True


def test_llm_adoption_readme_mentions():
    """Test detection of LLM mentions in README."""
    readme_content = """
    # Project
    This project uses GitHub Copilot for development.
    """
    with patch("ingest.Path.read_text", return_value=readme_content):
        flag = calculate_llm_adoption_flag("", [], [])
        assert flag is True


def test_llm_adoption_negative_case():
    """Test that repos without signals return False."""
    commits = [{"commit": {"message": "fix: bug"}} for _ in range(20)]
    flag = calculate_llm_adoption_flag("", commits, [])
    assert flag is False
