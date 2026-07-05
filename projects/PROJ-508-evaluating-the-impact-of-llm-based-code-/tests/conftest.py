"""
Pytest configuration and shared fixtures for the research pipeline.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure project root is in path for imports during tests
@pytest.fixture(autouse=True)
def add_project_root():
    root = Path(__file__).parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    yield
    if str(root) in sys.path:
        sys.path.remove(str(root))

@pytest.fixture
def sample_pr_data():
    """Mock PR data for testing metrics calculations."""
    return {
        "number": 101,
        "state": "closed",
        "created_at": "2023-01-01T00:00:00Z",
        "merged_at": "2023-01-01T12:00:00Z",
        "comments": 5,
        "review_threads": [
            {"comments": 2, "path": "file1.py"},
            {"comments": 1, "path": "file2.py"}
        ],
        "commits": [
            {"sha": "abc123", "message": "Fix bug in login", "stats": {"additions": 10, "deletions": 5, "total": 15}},
            {"sha": "def456", "message": "Refactor utils", "stats": {"additions": 20, "deletions": 10, "total": 30}}
        ]
    }

@pytest.fixture
def sample_repo_data():
    """Mock repository data for testing ingestion logic."""
    return {
        "name": "test-repo",
        "language": "Python",
        "topics": ["machine-learning", "llm"],
        "files": {
            ".cursorrules": "some rules",
            "README.md": "This project uses Copilot.",
            "CONTRIBUTING.md": "No mentions here."
        },
        "commit_messages": [
            "Initial commit",
            "Update docs",
            "Copilot suggestion applied",
            "Fix typo",
            "Another fix",
            "Refactor",
            "Copilot fix",
            "Hotfix",
            "Patch update",
            "Feature add",
            "More code",
            "Final commit",
            "Cleanup",
            "Docs update",
            "Bug fix"
        ]
    }
