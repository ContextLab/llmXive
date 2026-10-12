"""Create and verify the PROJ-874 project directory structure (T001a).

Creates the required directories:
  code/, data/raw/, data/processed/, data/results/, tests/, docs/, contracts/
and prints an `ls -R` style listing of the full hierarchy as the task's
deliverable evidence.
"""

import os
import sys
from pathlib import Path

from llmxive_toolkit import paths

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/processed",
    "data/results",
    "tests",
    "docs",
    "contracts",
]


def create_directory_structure(base_dir: Path) -> None:
    """Create the required project directory structure for PROJ-874.

    Args:
        base_dir: The root directory where the project structure is created.
    """
    for rel in REQUIRED_DIRS:
        (base_dir / rel).mkdir(parents=True, exist_ok=True)


def verify_structure(base_dir: Path) -> None:
    """Verify all required directories exist; abort loudly otherwise."""
    missing = [rel for rel in REQUIRED_DIRS if not (base_dir / rel).is_dir()]
    if missing:
        raise RuntimeError(f"Missing required directories: {missing}")


def print_listing(base_dir: Path) -> None:
    """Print an `ls -R` style listing of the project tree."""
    print(f"$ ls -R {base_dir}")
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = sorted(
            d for d in dirs if d not in {"venv", "__pycache__", ".git"}
        )
        rel_root = Path(root).relative_to(base_dir)
        label = "." if str(rel_root) == "." else str(rel_root)
        print(f"\n{base_dir / rel_root}:" if str(rel_root) != "." else f"{base_dir}:")
        entries = sorted(dirs + files)
        if entries:
            print("  " + "  ".join(entries))
        else:
            print("  (empty)")


def main() -> None:
    base_dir = paths.root
    create_directory_structure(base_dir)
    verify_structure(base_dir)
    print_listing(base_dir)
    print("\nAll required directories exist:")
    for rel in REQUIRED_DIRS:
        print(f"  {rel}/")
    print("T001a directory structure verified.")


if __name__ == "__main__":
    main()