import os
import sys
from pathlib import Path

def create_logs_directory(base_path: Path) -> None:
    """
    Creates the logs directory and archive subdirectory.
    Expected: logs/, logs/archive/
    """
    logs_path = base_path / "logs"
    archive_path = logs_path / "archive"
    
    logs_path.mkdir(parents=True, exist_ok=True)
    archive_path.mkdir(parents=True, exist_ok=True)
    
    print(f"Created logs directory: {logs_path}")
    print(f"Created logs/archive directory: {archive_path}")

def main() -> None:
    project_root = Path.cwd()
    project_id = "PROJ-756-assessing-dataset-imbalance-effects-on-m"
    base_path = project_root / "projects" / project_id
    create_logs_directory(base_path)

if __name__ == "__main__":
    main()