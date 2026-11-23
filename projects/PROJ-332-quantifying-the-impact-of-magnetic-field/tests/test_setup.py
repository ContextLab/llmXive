import os
from pathlib import Path

def test_project_directories_exist():
    """Verify that the required project directories exist."""
    root = Path(__file__).parent.parent
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "outputs",
        "tests",
        "contracts",
        ".github/workflows",
    ]

    missing = []
    for dir_name in required_dirs:
        full_path = root / dir_name
        if not full_path.exists():
            missing.append(dir_name)

    assert len(missing) == 0, f"Missing directories: {missing}"
