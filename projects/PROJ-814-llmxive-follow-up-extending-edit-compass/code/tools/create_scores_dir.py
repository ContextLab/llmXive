"""
Tool to create the data/scores directory.
This script ensures the `data/scores` directory exists at the project root.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine project root (assuming script is in code/tools/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    scores_dir = project_root / "data" / "scores"

    try:
        scores_dir.mkdir(parents=True, exist_ok=True)
        print(f"Successfully ensured directory exists: {scores_dir}")
        return 0
    except PermissionError:
        print(f"Error: Permission denied when creating directory: {scores_dir}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error creating directory {scores_dir}: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())