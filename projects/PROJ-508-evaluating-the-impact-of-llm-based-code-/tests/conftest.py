"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def add_src_to_path():
    project_root = Path(__file__).parent.parent
    src_path = project_root / "code"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    yield
    if str(src_path) in sys.path:
        sys.path.remove(str(src_path))

@pytest.fixture
def sample_repo_data():
    """Fixture providing a mock repository data structure for testing."""
    return {
        "full_name": "test/repo",
        "language": "Python",
        "commits": [
            {"message": "Fix bug in login", "sha": "abc123", "stats": {"additions": 10, "deletions": 5}},
            {"message": "Refactor auth module", "sha": "def456", "stats": {"additions": 50, "deletions": 20}},
            {"message": "Update Copilot settings", "sha": "ghi789", "stats": {"additions": 2, "deletions": 1}},
        ],
        "pull_requests": [
            {
                "number": 101,
                "state": "closed",
                "created_at": "2023-01-01T00:00:00Z",
                "merged_at": "2023-01-02T00:00:00Z",
                "comments": [
                    {"body": "Looks good"},
                    {"body": "Can we optimize this?"},
                ],
                "review_comments": [
                    {"body": "Nit: variable name"},
                ],
                "commits": ["abc123", "def456"],
            }
        ],
        "files": [
            {"name": ".cursorrules", "path": ".cursorrules"},
            {"name": "README.md", "path": "README.md"},
        ],
    }
