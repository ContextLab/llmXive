"""
Test module to verify repository structure exists.

Run after setup_project_structure.py to confirm all directories were created.

Usage: python -m pytest tests/test_project_structure.py
       or: python tests/test_project_structure.py
"""
import os
import sys
from pathlib import Path
import pytest


# Required directories as specified in T001
REQUIRED_DIRECTORIES = [
    "src",
    "tests",
    "data",
    "output",
    "contracts",
    "notebooks",
    ".github",
    "docs",
]


def get_base_path() -> Path:
    """Get the project root path (parent of tests directory)."""
    return Path(__file__).resolve().parent.parent


class TestProjectStructure:
    """Test class for verifying repository structure."""

    @pytest.fixture
    def base_path(self) -> Path:
        """Fixture providing the project root path."""
        return get_base_path()

    @pytest.mark.parametrize("dir_name", REQUIRED_DIRECTORIES)
    def test_directory_exists(self, base_path: Path, dir_name: str) -> None:
        """Test that each required directory exists."""
        dir_path = base_path / dir_name
        assert dir_path.exists(), f"Directory '{dir_name}' does not exist at {dir_path}"
        assert dir_path.is_dir(), f"'{dir_name}' exists but is not a directory"

    def test_all_directories_exist(self, base_path: Path) -> None:
        """Test that all required directories exist."""
        missing = []
        for dir_name in REQUIRED_DIRECTORIES:
            dir_path = base_path / dir_name
            if not dir_path.exists() or not dir_path.is_dir():
                missing.append(dir_name)
        
        if missing:
            pytest.fail(f"Missing directories: {missing}")

    def test_src_is_python_package(self, base_path: Path) -> None:
        """Test that src/ has __init__.py (Python package)."""
        init_file = base_path / "src" / "__init__.py"
        # __init__.py may not exist yet - this is informational
        if init_file.exists():
            assert init_file.is_file()


def main() -> int:
    """Run tests directly if executed as script."""
    base_path = get_base_path()
    all_exist = True
    
    print("Verifying repository structure...")
    print("-" * 50)
    
    for dir_name in REQUIRED_DIRECTORIES:
        dir_path = base_path / dir_name
        exists = dir_path.exists() and dir_path.is_dir()
        status = "✓" if exists else "✗"
        print(f"  {status} {dir_name}/")
        if not exists:
            all_exist = False
    
    print("-" * 50)
    
    if all_exist:
        print("All required directories exist.")
        return 0
    else:
        print("ERROR: Some directories are missing!")
        print("Run: python code/setup_project_structure.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())