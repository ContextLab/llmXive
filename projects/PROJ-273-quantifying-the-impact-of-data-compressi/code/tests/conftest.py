import pytest
import sys
from pathlib import Path

# Ensure the project root and src directory are in the path
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add project paths to sys.path for imports."""
    root = Path(__file__).parent.parent
    src_path = root / "src"
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    yield
    # Cleanup not strictly necessary as sys.path is process-local

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup global test environment variables if needed."""
    import os
    os.environ.setdefault("TEST_MODE", "true")
    yield
    # Teardown if necessary
