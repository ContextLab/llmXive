"""
Pytest configuration and shared fixtures for the test suite.
"""
import os
import sys
import logging
from pathlib import Path

import pytest

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    project_root = Path(__file__).parent.parent
    if str(project_root / "code") not in sys.path:
        sys.path.insert(0, str(project_root / "code"))
    yield
    if str(project_root / "code") in sys.path:
        sys.path.remove(str(project_root / "code"))

@pytest.fixture
def sample_repo_data():
    """Fixture providing a mock repository data structure for ingestion tests."""
    return {
        "full_name": "test/repo",
        "stargazers_count": 100,
        "language": "Python",
        "default_branch": "main",
    }

@pytest.fixture
def sample_pr_data():
    """Fixture providing a mock PR data structure for metrics tests."""
    return {
        "number": 123,
        "state": "closed",
        "merged_at": "2023-10-01T12:00:00Z",
        "created_at": "2023-09-25T10:00:00Z",
        "merged": True,
        "comments": 5,
        "review_comments": 3,
    }

@pytest.fixture
def sample_commit_data():
    """Fixture providing a mock commit data structure for adoption tests."""
    return {
        "sha": "abc123",
        "commit": {
            "message": "feat: add new feature with Copilot assistance",
            "author": {"name": "Test User"},
        },
    }
