import os
import sys
from pathlib import Path
from typing import List

from utils.config import get_project_root, ensure_dir

def create_directory(path: Path) -> None:
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def verify_directory(path: Path) -> bool:
    """Verify that a directory exists using os.path.exists."""
    return os.path.exists(path) and path.is_dir()

def main() -> int:
    """
    Create and verify tests/unit/ and tests/integration/ subdirectories.
    
    Returns:
        int: 0 on success, 1 on failure.
    """
    project_root = get_project_root()
    tests_root = project_root / "tests"
    unit_dir = tests_root / "unit"
    integration_dir = tests_root / "integration"

    # Ensure tests root exists first
    ensure_dir(tests_root)

    # Create subdirectories
    create_directory(unit_dir)
    create_directory(integration_dir)

    # Verify creation using os.path.exists as required
    if not verify_directory(unit_dir):
        raise FileNotFoundError(f"Failed to create or verify directory: {unit_dir}")
    
    if not verify_directory(integration_dir):
        raise FileNotFoundError(f"Failed to create or verify directory: {integration_dir}")

    print(f"Successfully created and verified: {unit_dir}")
    print(f"Successfully created and verified: {integration_dir}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
