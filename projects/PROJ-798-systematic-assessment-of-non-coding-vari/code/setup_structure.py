"""
setup_structure.py

Script to create the required project directory layout and generate a
manifest file listing all directories. This satisfies task T001.

The script:
  1. Ensures the following directories exist:
      - code/
      - code/analysis/
      - code/data_ingestion/
      - code/scoring/
      - code/utils/
      - data/
      - data/raw/
      - data/derived/
      - data/results/
      - tests/
      - tests/unit/
      - tests/integration/
      - tests/contract/
  2. Runs the verification command:
      find code data tests -type d | sort > data/results/structure_manifest.txt
  3. Writes the sorted list of directories to
     data/results/structure_manifest.txt.

The script is deliberately side‑effect free aside from creating the
directories and the manifest file; it raises on any failure so that the
CI runner can detect problems.
"""

import subprocess
import sys
from pathlib import Path

def _ensure_directories():
    """Create all required directories if they do not already exist."""
    dirs = [
        "code",
        "code/analysis",
        "code/data_ingestion",
        "code/scoring",
        "code/utils",
        "data",
        "data/raw",
        "data/derived",
        "data/results",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def _generate_manifest():
    """
    Run the verification command and write the sorted list of directories
    to data/results/structure_manifest.txt.
    """
    try:
        # Use subprocess to invoke the system `find` command.
        result = subprocess.run(
            ["find", "code", "data", "tests", "-type", "d"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Error running find: {exc}", file=sys.stderr)
        raise

    # Sort the output lines to match the verification step.
    dirs = sorted(line.strip() for line in result.stdout.splitlines() if line.strip())
    manifest_path = Path("data/results/structure_manifest.txt")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(dirs) + "\n")
    print(f"Manifest written to {manifest_path}")

def main():
    """Entry point."""
    _ensure_directories()
    _generate_manifest()

if __name__ == "__main__":
    main()
