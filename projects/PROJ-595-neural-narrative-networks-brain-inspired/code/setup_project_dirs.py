"""T001: Create the project directory skeleton.

Ensures the following directories exist (relative to the project root):
  code/, data/raw/, data/processed/, data/results/, tests/

Also verifies that code/__init__.py exists (created separately).
Exits non-zero if any directory cannot be created.
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DIRS = [
    PROJECT_ROOT / "code",
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
    PROJECT_ROOT / "data" / "results",
    PROJECT_ROOT / "tests",
]

def main() -> int:
    failures = []
    for d in REQUIRED_DIRS:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception as exc:  # pragma: no cover
            print(f"ERROR: could not create {d}: {exc}", file=sys.stderr)
            failures.append(str(d))
        if d.is_dir():
            # keep empty dirs representable in git
            keep = d / ".gitkeep"
            if not any(d.iterdir()):
                keep.touch()
            print(f"OK: {d}")
        else:
            failures.append(str(d))

    init_file = PROJECT_ROOT / "code" / "__init__.py"
    if not init_file.exists():
        print(f"ERROR: missing {init_file}", file=sys.stderr)
        failures.append(str(init_file))
    else:
        print(f"OK: {init_file}")

    if failures:
        print(f"FAILED: {failures}", file=sys.stderr)
        return 1
    print("All required project directories are present.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
