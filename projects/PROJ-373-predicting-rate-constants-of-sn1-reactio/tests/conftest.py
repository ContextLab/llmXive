"""
Pytest configuration and fixtures.
Ensures jsonschema is available and sets up test environment.
"""
import pytest
import sys
from pathlib import Path

# Ensure project root is in path for imports if needed
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def pytest_configure(config):
    """Configure pytest markers if any."""
    config.addinivalue_line(
        "markers", "contract: mark test as a contract test against schema"
    )
