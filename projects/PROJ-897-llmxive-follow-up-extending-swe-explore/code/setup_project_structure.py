"""
T001a: Create Project Structure.

Creates the required directory scaffold for the llmXive follow-up project:
  - code/
  - data/raw/, data/curated/, data/results/
  - tests/unit/, tests/integration/, tests/contract/
  - specs/001-llmxive-follow-up-extending-swe-explore/contracts/
  - state/ (checksum manifests per Constitution Principle V)

Each directory is created (idempotently), a .gitkeep placeholder is added so
empty directories are tangible on disk and in version control, and the full
structure is verified at the end. The script exits non-zero if verification
fails.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    "code",
    "data/raw",
    "data/curated",
    "data/results",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "specs/001-llmxive-follow-up-extending-swe-explore/contracts",
    "state",
]

def create_structure() -> None:
    """Create every required directory and a .gitkeep marker inside it."""
    for rel in REQUIRED_DIRS:
        target = PROJECT_ROOT / rel
        if target.exists():
            if not target.is_dir():
                raise NotADirectoryError(
                    f"Path exists but is not a directory: {target}"
                )
            print(f"[exists] {rel}/")
        else:
            target.mkdir(parents=True, exist_ok=True)
            print(f"[created] {rel}/")
        keep = target / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")

def verify_structure() -> bool:
    """Verify all required directories exist. Returns True on success."""
    ok = True
    for rel in REQUIRED_DIRS:
        target = PROJECT_ROOT / rel
        if target.is_dir():
            print(f"[ok] {rel}/")
        else:
            print(f"[MISSING] {rel}/", file=sys.stderr)
            ok = False
    return ok

def main() -> int:
    print(f"Project root: {PROJECT_ROOT}")
    print("Creating project structure (T001a)...")
    create_structure()
    print("\nVerifying structure...")
    if verify_structure():
        print("\nT001a COMPLETE: directory structure created and verified.")
        return 0
    print("\nT001a FAILED: some directories are missing.", file=sys.stderr)
    return 1

if __name__ == "__main__":
    sys.exit(main())