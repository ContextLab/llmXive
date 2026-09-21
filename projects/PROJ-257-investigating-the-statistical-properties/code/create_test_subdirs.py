"""
Task T001d: Create test subdirectories and .gitkeep files.

Creates the following structure:
- tests/unit/.gitkeep
- tests/integration/.gitkeep
- tests/contract/.gitkeep
"""
import os
import sys
from pathlib import Path


def create_test_subdirectories(base_path: Path) -> None:
    """Create unit, integration, and contract subdirectories with .gitkeep files."""
    subdirs = ["unit", "integration", "contract"]

    for subdir_name in subdirs:
        subdir_path = base_path / subdir_name
        subdir_path.mkdir(parents=True, exist_ok=True)

        gitkeep_path = subdir_path / ".gitkeep"
        gitkeep_path.touch()
        print(f"Created: {gitkeep_path}")


def main() -> None:
    """Entry point for T001d."""
    # Determine project root (assuming script is in code/)
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    tests_dir = project_root / "tests"

    if not tests_dir.exists():
        print(f"Error: {tests_dir} does not exist. Run T001c first.")
        sys.exit(1)

    create_test_subdirectories(tests_dir)
    print("T001d completed successfully.")


if __name__ == "__main__":
    main()
