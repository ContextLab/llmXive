"""T002: Create data/raw/ and data/processed/ directories.

Creates the two required data directories relative to the project root
(the parent of the code/ directory containing this file) and verifies
they exist afterwards, exiting non-zero on failure.
"""
import sys
from pathlib import Path

def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    targets = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
    ]
    for d in targets:
        d.mkdir(parents=True, exist_ok=True)
    # Verify
    for d in targets:
        if not (d.is_dir()):
            print(f"ERROR: failed to create {d}", file=sys.stderr)
            return 1
        print(f"OK: {d} exists")
    return 0

if __name__ == "__main__":
    sys.exit(main())