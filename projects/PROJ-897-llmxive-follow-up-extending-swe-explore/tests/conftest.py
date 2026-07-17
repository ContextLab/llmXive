"""
Pytest configuration and fixtures for the llmXive project.

This file configures the test environment, ensuring that the project root
is in the Python path so that imports from `code/` work correctly.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Optional: Define fixtures here if needed for multiple tests
# Example:
# @pytest.fixture
# def sample_issue():
#     return {...}

def pytest_configure(config):
    """Configure pytest markers or global settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "contract: marks contract tests verifying schema compliance"
    )