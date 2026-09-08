import pytest
import sys
from pathlib import Path

@pytest.fixture
def add_src_to_path():
    """Add the project src directory to sys.path for imports."""
    root = Path(__file__).parent.parent
    src_path = root / "code" / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    yield
    # Cleanup if necessary, though sys.path is usually global per session

@pytest.fixture
def sample_data_path():
    """Return the path to the sample data directory."""
    root = Path(__file__).parent.parent
    return root / "code" / "data" / "sample"