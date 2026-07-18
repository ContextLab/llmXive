"""
Pytest configuration and fixtures for the llmXive project.

This file configures the test environment, ensuring that:
1. The project root is on the PYTHONPATH for imports like `from config import ...`.
2. Required directories (`data/raw`, `data/processed`) exist before tests run.
3. Common fixtures (e.g., sample trajectory data) are available.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project root (parent of 'tests') is in sys.path
# so that imports like `from config import ensure_directories` work.
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config import ensure_directories


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Automatically run before any tests to ensure required directories exist.
    This mirrors the setup done in production but ensures tests have a clean slate.
    """
    # Call the project's configuration function to ensure directories exist
    ensure_directories()
    # Yield control to pytest; any code after is teardown (optional)
    yield


@pytest.fixture
def sample_trajectory_data():
    """
    Returns a minimal valid trajectory dictionary structure for testing.
    This is a mock object, not real data from the dataset, used for unit testing logic.
    """
    return {
        "id": "test-trajectory-001",
        "spans": [
            {
                "id": "span-1",
                "text": "The agent begins the research process.",
                "references": [],
                "error_type": None
            },
            {
                "id": "span-2",
                "text": "It cites the initial paper from Span-1.",
                "references": ["span-1"],
                "error_type": None
            },
            {
                "id": "span-3",
                "text": "A new branch is created based on Span-2.",
                "references": ["span-2"],
                "error_type": "hallucination"
            }
        ],
        "metadata": {
            "source": "tebench",
            "split": "train"
        }
    }


@pytest.fixture
def temp_output_dir(tmp_path):
    """
    Provides a temporary directory for tests that need to write files.
    """
    return tmp_path
