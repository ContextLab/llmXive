"""T001: Create the project directory layout.

Creates the directories required by the project structure:
code, utils, tests/unit, tests/integration,
data/raw, data/interim, data/processed.
Idempotent: safe to run multiple times.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES = [
    "code",
    "code/utils",
    "utils",
    "tests",
    "tests/unit",
    "tests/integration",
    "data/raw",
    "data/interim",
    "data/processed",
]

def create_directories(root: Path = PROJECT_ROOT) -> list:
    """Create all required directories under root; return created paths."""
    created = []
    for rel in DIRECTORIES:
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        if not d.is_dir():
            raise RuntimeError(f"Failed to create directory: {d}")
        created.append(d)
    return created

def main() -> int:
    dirs = create_directories()
    for d in dirs:
        print(f"OK {d.relative_to(PROJECT_ROOT)}")
    # Verify all required directories exist (T026-style check)
    missing = [str(root_dir) for root_dir in dirs if not root_dir.is_dir()]
    if missing:
        print(f"MISSING: {missing}", file=sys.stderr)
        return 1
    print("All project directories created and verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
