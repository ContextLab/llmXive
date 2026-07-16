"""
Pytest configuration and fixtures for the llmXive project.
"""
import sys
import os
from pathlib import Path

# Add the 'code' directory to the path so imports work in tests
# This assumes the tests are run from the project root or the path is set correctly
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"

if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Ensure logging is configured for tests
def pytest_configure(config):
    # Configure default logging for tests to avoid silent failures
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
