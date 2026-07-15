"""
Script to initialize the project directory structure.
Creates: code/, data/raw/, data/processed/, tests/, docs/, results/
"""
import os
import sys
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "docs",
        "results",
        "code/utils",  # Subdirectory needed for T001b
        "tests/integration",
        "tests/unit",
    ]

    created = 0
    skipped = 0

    for d in dirs:
        target = root / d
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            print(f"Created: {target.relative_to(root)}")
            created += 1
        else:
            skipped += 1

    print(f"\nDone. Created {created} directories, skipped {skipped} existing.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
