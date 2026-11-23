"""T001a: Create the project directory structure.

Creates the required directories:
  code/, tests/, data/raw, data/processed, results/plots,
  specs/001-coral-resilience-prediction/

Each directory is populated with a .gitkeep placeholder file so the
structure is committed to version control, and a verification log is
written to results/plots/../structure_verification.log (results/).
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "code",
    "tests",
    "data/raw",
    "data/processed",
    "results/plots",
    "specs/001-coral-resilience-prediction",
]

LOG_PATH = PROJECT_ROOT / "results" / "structure_verification.log"


def create_structure(root: Path = PROJECT_ROOT) -> None:
    """Create all required directories and .gitkeep files."""
    for rel in REQUIRED_DIRS:
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")


def verify_structure(root: Path = PROJECT_ROOT) -> list:
    """Return list of missing directories (empty if all present)."""
    missing = []
    for rel in REQUIRED_DIRS:
        if not (root / rel).is_dir():
            missing.append(rel)
    return missing


def main() -> int:
    create_structure()
    missing = verify_structure()
    lines = ["T001a project structure verification"]
    for rel in REQUIRED_DIRS:
        full = PROJECT_ROOT / rel
        status = "OK" if full.is_dir() else "MISSING"
        lines.append(f"{status}: {rel} -> {full}")
    if missing:
        lines.append(f"FAILED: missing directories: {missing}")
        print("\n".join(lines))
        return 1
    lines.append("ALL DIRECTORIES PRESENT")
    print("\n".join(lines))
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())