"""
Utility script to ensure the top-level `code/` directory exists.
This is part of task T001a.
"""

from pathlib import Path
import sys

def main() -> int:
    """
    Create the `code/` directory at the repository root if it does not exist.
    Returns 0 on success, non‑zero on failure.
    """
    # The repository root is the parent of this file's parent (i.e., two levels up)
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    try:
        code_dir.mkdir(parents=True, exist_ok=True)
        print(f"Ensured code directory exists at: {code_dir}")
        return 0
    except Exception as exc:
        print(f"Error creating code directory: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())