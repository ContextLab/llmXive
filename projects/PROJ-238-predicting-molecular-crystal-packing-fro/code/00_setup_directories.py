"""T001.1: Create repository root directories.

Creates the project's root directory structure required by the pipeline:
code/, data/, results/, and state/ (plus state/projects/ for artifact
hash bookkeeping). Idempotent: re-running does not fail or overwrite.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES = [
    ROOT / "code",
    ROOT / "data",
    ROOT / "results",
    ROOT / "state",
    ROOT / "state" / "projects",
]

def create_directories(directories):
    created = []
    for d in directories:
        d.mkdir(parents=True, exist_ok=True)
        marker = d / ".gitkeep"
        if not marker.exists():
            marker.write_text("", encoding="utf-8")
        created.append(str(d))
    return created

def main():
    created = create_directories(DIRECTORIES)
    for path in created:
        print(f"OK directory ready: {path}")
    # Verification: all directories exist
    missing = [str(d) for d in DIRECTORIES if not d.is_dir()]
    if missing:
        print(f"FATAL: missing directories: {missing}", file=sys.stderr)
        sys.exit(1)
    print("All root directories created and verified.")

if __name__ == "__main__":
    main()