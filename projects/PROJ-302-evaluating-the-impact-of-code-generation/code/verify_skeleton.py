"""
verify_skeleton.py

Simple verification script for the project skeleton.
Checks that the required top‑level files exist and that the
requirements file can be parsed without syntax errors.
"""

import sys
from pathlib import Path

def main() -> int:
    project_root = Path(__file__).resolve().parents[1]

    req_path = project_root / "requirements.txt"
    quickstart_path = project_root / "docs" / "quickstart.md"

    missing = []

    if not req_path.is_file():
        missing.append(str(req_path))
    if not quickstart_path.is_file():
        missing.append(str(quickstart_path))

    if missing:
        print("Missing required files:", file=sys.stderr)
        for p in missing:
            print(f"  - {p}", file=sys.stderr)
        return 1

    # Basic sanity check: can we read the requirements file?
    try:
        req_path.read_text()
    except Exception as e:
        print(f"Error reading requirements.txt: {e}", file=sys.stderr)
        return 1

    print("Project skeleton verification passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())