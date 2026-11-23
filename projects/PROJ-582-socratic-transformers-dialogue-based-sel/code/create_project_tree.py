"""
Utility script to create the canonical project directory tree for the
Socratic Transformers project.

Required directories (relative to the location of this script, i.e. the
``code`` folder):
    - src
    - data/raw
    - data/processed
    - data/results
    - tests
    - state

The script is idempotent: running it multiple times will not raise
errors if the directories already exist.
"""
import sys
from pathlib import Path

def create_directories(base_path: Path) -> None:
    """
    Create the required directory hierarchy under ``base_path``.

    Parameters
    ----------
    base_path : Path
        The root ``code`` directory of the project.
    """
    # List of required directories relative to ``base_path``
    required_dirs = [
        Path("src"),
        Path("data/raw"),
        Path("data/processed"),
        Path("data/results"),
        Path("tests"),
        Path("state"),
    ]

    for rel_dir in required_dirs:
        dir_path = base_path / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        # Ensure a .gitkeep file exists so empty directories are tracked
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

def main() -> int:
    """
    Entry point for the script.

    Returns
    -------
    int
        Exit status (0 = success, non‑zero = failure).
    """
    try:
        # ``__file__`` points to this script inside the ``code`` folder
        code_root = Path(__file__).resolve().parent
        create_directories(code_root)
        return 0
    except Exception as e:
        print(f"Error creating project directories: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
