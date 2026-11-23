import os
import sys
import pytest
from pathlib import Path

# Add the project root to sys.path so imports work correctly during tests
@pytest.fixture(autouse=True, scope="session")
def add_src_to_path():
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    return str(src_path)

@pytest.fixture(scope="session")
def session_root():
    return Path(__file__).parent.parent
