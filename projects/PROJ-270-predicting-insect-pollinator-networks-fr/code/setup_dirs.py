"""
T001a: Create the standard project directory structure.

Creates (idempotently, with parents):
  code/ code/utils/ code/contracts/ data/raw/ data/processed/
  tests/ docs/ results/

Run: python code/setup_dirs.py
"""
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    required_dirs = [
        "code",
        "code/utils",
        "code/contracts",
        "data",
        "data/raw",
        "data/processed",
        "tests",
        "docs",
        "results",
    ]
    for d in required_dirs:
        (project_root / d).mkdir(parents=True, exist_ok=True)

    # Verify existence (fail loudly if anything is missing)
    missing = [d for d in required_dirs if not (project_root / d).is_dir()]
    if missing:
        print(f"ERROR: directories missing after creation: {missing}", file=sys.stderr)
        return 1

    print(f"Directory structure verified at {project_root}")
    for d in required_dirs:
        print(f"  OK: {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
