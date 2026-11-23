"""
Helper module to create logs directory and archive.
"""
import os
import sys
from pathlib import Path

def create_logs_directory():
    """
    Create logs directory, archive subdirectory, and init files.
    """
    project_root = Path.cwd()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    archive_dir = logs_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # __init__.py
    init_file = logs_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Logs package\n")
    
    # .gitkeep in archive
    gitkeep = archive_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("# Archived logs\n")
    
    print(f"Created logs directory: {logs_dir}")

def main():
    create_logs_directory()

if __name__ == "__main__":
    main()
