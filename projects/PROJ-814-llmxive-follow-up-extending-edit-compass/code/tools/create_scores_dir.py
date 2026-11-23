import os
import sys
from pathlib import Path

def main():
    """
    Create the data/scores directory and add a .gitkeep file.
    This task (T001i) prepares the storage location for scoring results.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    scores_dir = project_root / "data" / "scores"

    if not scores_dir.exists():
        scores_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {scores_dir}")
    else:
        print(f"Directory already exists: {scores_dir}")

    gitkeep = scores_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()
        print(f"Created .gitkeep in: {scores_dir}")
    else:
        print(f".gitkeep already exists in: {scores_dir}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
