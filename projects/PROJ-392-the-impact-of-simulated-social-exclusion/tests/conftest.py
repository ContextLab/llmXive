"""
Pytest configuration and fixtures for the project.
"""
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports during testing
# This helps if tests are run from the project root
def pytest_configure(config):
    # Add the code directory to sys.path if not already present
    code_dir = Path(__file__).parent.parent / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))