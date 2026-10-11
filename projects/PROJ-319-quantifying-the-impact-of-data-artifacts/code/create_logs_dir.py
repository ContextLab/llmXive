"""
Script to create the project 'logs' directory.
This satisfies task T001a4 which requires the existence of a logs/ directory.
"""

from pathlib import Path

# Import get_project_root to reliably locate the project root.
try:
    from code.config import get_project_root
except ImportError:
    # Fallback if the module path is not set; assume this script lives in <root>/code/
    import sys
    root_path = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root_path))
    from config import get_project_root


def create_logs_directory() -> None:
    """
    Ensure that the 'logs' directory exists at the project root.
    """
    root: Path = get_project_root()
    logs_dir = root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)


def main() -> None:
    create_logs_directory()
    print("Logs directory created (or already existed).")


if __name__ == "__main__":
    main()