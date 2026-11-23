"""Create and verify the project directory structure (Task T001).

Creates the directories required by Plan.md:
code/, tests/, data/raw/, data/processed/, data/validation/,
data/models/, data/results/, data/logs/, docs/, specs/

Then verifies them with the equivalent of `ls -d code/ tests/ data/ docs/ specs/`
and exits 0 on success.
"""
import sys
from pathlib import Path

from config import ensure_directories


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    if not ensure_directories():
        print("ERROR: failed to create required directories", file=sys.stderr)
        return 1

    required = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/validation",
        "data/models",
        "data/results",
        "data/logs",
        "docs",
        "specs",
    ]
    print(f"Project root: {project_root}")
    for rel in required:
        p = project_root / rel
        if not p.is_dir():
            print(f"ERROR: missing directory {rel}", file=sys.stderr)
            return 1
        print(f"{rel}/")

    # Verification equivalent to: ls -d code/ tests/ data/ docs/ specs/
    verify = ["code", "tests", "data", "docs", "specs"]
    print("\nVerification: ls -d " + " ".join(f"{d}/" for d in verify))
    for d in verify:
        p = project_root / d
        if not p.is_dir():
            print(f"ERROR: verification failed for {d}/", file=sys.stderr)
            return 1
        print(f"{p}")
    print("Verification passed (exit code 0)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
