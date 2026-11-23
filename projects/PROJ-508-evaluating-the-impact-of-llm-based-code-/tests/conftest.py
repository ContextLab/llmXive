"""
Pytest configuration and shared fixtures.
"""
import pytest
import sys
from pathlib import Path

# Add the project root to the path to ensure imports work
# when running tests from the command line.
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """
    Automatically add the project root to sys.path for imports.
    """
    root_dir = Path(__file__).parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))
    yield
    # Cleanup if necessary (though usually not needed for path insertion)

@pytest.fixture
def sample_repo_data():
    """
    Fixture providing a minimal mock of repository data structure.
    Used for testing ingestion and metrics logic without hitting the API.
    """
    return {
        "full_name": "test/repo",
        "stargazers_count": 100,
        "language": "Python",
        "default_branch": "main",
        "has_issues": True
    }

@pytest.fixture
def sample_pr_data():
    """
    Fixture providing a minimal mock of PR data.
    """
    return {
        "number": 42,
        "title": "Test PR",
        "state": "closed",
        "merged": True,
        "created_at": "2023-01-01T00:00:00Z",
        "merged_at": "2023-01-02T00:00:00Z",
        "user": {"login": "test_user"}
    }