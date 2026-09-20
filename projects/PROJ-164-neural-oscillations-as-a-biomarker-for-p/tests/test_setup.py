import os
import sys
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_project_structure_exists():
    """Verify that all required directories from T001a exist."""
    project_root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "data/synthetic",
        "models",
        "docs",
        "docs/contracts",
        "state/projects",
        "logs"
    ]
    
    missing_dirs = []
    for dir_name in required_dirs:
        full_path = project_root / dir_name
        if not full_path.exists():
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        pytest.fail(f"The following required directories are missing: {missing_dirs}")
    else:
        # Log success
        print("All required project directories exist.")
