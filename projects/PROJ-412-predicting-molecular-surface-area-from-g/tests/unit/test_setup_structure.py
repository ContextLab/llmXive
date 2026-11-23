import os
import sys
from pathlib import Path
import pytest
import tempfile
import shutil

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.setup_structure import create_directories

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as project root for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir)

def test_create_directories(temp_project_root):
    """Test that create_directories creates all required folders."""
    required_dirs = [
        "code/data",
        "code/models",
        "code/eval",
        "code/utils",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/splits",
        "results/reports",
        "results/plots"
    ]
    
    # Verify directories don't exist before creation (optional, just for cleanliness)
    for d in required_dirs:
        assert not (temp_project_root / d).exists(), f"Directory {d} already exists in temp root"

    # Run the function
    create_directories(temp_project_root)

    # Verify all directories exist
    for d in required_dirs:
        full_path = temp_project_root / d
        assert full_path.exists(), f"Directory {d} was not created"
        assert full_path.is_dir(), f"{d} exists but is not a directory"

def test_create_directories_idempotent(temp_project_root):
    """Test that running create_directories twice does not cause errors."""
    create_directories(temp_project_root)
    # Running again should not raise an exception
    create_directories(temp_project_root)
    
    # Verify structure still intact
    assert (temp_project_root / "code/data").exists()
    assert (temp_project_root / "results/plots").exists()
