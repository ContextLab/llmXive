import os
import pytest
from pathlib import Path

# Helper to get project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_required_directories_exist():
    """Verify that T001 created the required directory structure."""
    required_dirs = [
        "code",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs/figures",
        "state",
    ]
    
    missing = []
    for d in required_dirs:
        path = PROJECT_ROOT / d
        if not path.exists() or not path.is_dir():
            missing.append(d)
    
    if missing:
        pytest.fail(f"Required directories missing: {missing}")
    
    # If we get here, all directories exist
    assert True