"""Create test directory structure for the project."""
import os
from pathlib import Path

def create_test_directories(root_dir: str = ".") -> None:
    """Create tests/ directory with contract/, integration/, unit/ subdirectories.
    
    Args:
        root_dir: Root directory path (defaults to current directory)
    """
    root = Path(root_dir)
    tests_dir = root / "tests"
    
    # Create main tests directory
    tests_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    subdirs = ["contract", "integration", "unit"]
    for subdir in subdirs:
        (tests_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py files for proper Python package structure
    (tests_dir / "__init__.py").touch()
    for subdir in subdirs:
        (tests_dir / subdir / "__init__.py").touch()
    
    print(f"Created test directory structure under: {tests_dir}")
    print(f"  - tests/contract/")
    print(f"  - tests/integration/")
    print(f"  - tests/unit/")

if __name__ == "__main__":
    create_test_directories()
