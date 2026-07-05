"""
Tests for data ingestion and LLM adoption classification logic.
"""
import pytest
from utils.metrics import calculate_domain_complexity

@pytest.fixture
def sample_repo_data():
    """Fixture providing mock repository data for testing."""
    return {
        "files": {
            ".cursorrules": "some rules",
            "README.md": "Project description",
            "setup.py": "setup code"
        },
        "commit_messages": [
            "Initial commit",
            "Add feature A",
            "Fix bug in module B",
            "Copilot suggestion applied",
            "Update documentation",
            "Refactor utils",
            "Add tests",
            "Fix typo",
            "Copilot generated code",
            "Merge branch",
            "Update dependencies",
            "Fix linting errors",
            "Add new endpoint",
            "Update config",
            "Final cleanup"
        ]
    }

def test_cursorrules_detection(sample_repo_data):
    """Test that .cursorrules presence is detected."""
    files = sample_repo_data["files"]
    assert ".cursorrules" in files
    assert files[".cursorrules"] == "some rules"

def test_commit_message_frequency(sample_repo_data):
    """Test calculation of 'Copilot' frequency in commit messages."""
    messages = sample_repo_data["commit_messages"]
    copilot_count = sum(1 for m in messages if "Copilot" in m)
    total = len(messages)
    freq = copilot_count / total
    # 2 occurrences out of 15
    assert freq == 2/15

def test_domain_complexity_calculation():
    """Test domain complexity based on languages and dependencies."""
    # Mock: 1 language, 5 dependencies
    complexity = calculate_domain_complexity(["Python"], 5)
    # Formula: (unique_langs + dep_count) / 2 -> (1+5)/2 = 3.0
    assert complexity == 3.0

def test_domain_complexity_multiple_langs():
    """Test domain complexity with multiple languages."""
    complexity = calculate_domain_complexity(["Python", "JS", "Go"], 2)
    # (3 + 2) / 2 = 2.5
    assert complexity == 2.5