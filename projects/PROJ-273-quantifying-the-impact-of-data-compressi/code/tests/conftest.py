"""
Pytest configuration and fixtures for the project.
"""
import pytest
import sys
from pathlib import Path

# Add the 'code' directory to the Python path so imports like `from src.data.download import ...` work
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_root = Path(__file__).parent.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    return code_root

@pytest.fixture(scope="session")
def setup_test_environment():
    """
    Setup any global test environment state if needed.
    Currently a placeholder for future test infrastructure.
    """
    return {"initialized": True}
