"""
Script to initialize project directory structure.

Creates all required directories for the llmXive pipeline and writes
a success log to data/.init_log.txt.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

def get_project_root() -> Path:
    """Return the root directory of the project."""
    # Assumes this script is at code/scripts/init_dirs.py
    return Path(__file__).resolve().parent.parent

def create_directories() -> list[Path]:
    """Create all required directories and return list of created paths."""
    root = get_project_root()
    
    # Define all required directories relative to root
    dirs = [
        "code",
        "data",
        "data/synthetic",
        "data/synthetic/raw",
        "data/synthetic/short_context",
        "data/results",
        "data/results/logs",
        "data/results/aggregated",
        "tests",
        "models",
        "data/assets",
    ]
    
    created_paths = []
    for dir_path in dirs:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(full_path)
        
    return created_paths

def write_init_log(created_paths: list[Path]) -> Path:
    """Write a success log to data/.init_log.txt."""
    root = get_project_root()
    log_path = root / "data" / ".init_log.txt"
    
    timestamp = datetime.now().isoformat()
    content = (
        f"Initialization completed at {timestamp}\n"
        f"Created {len(created_paths)} directories:\n"
        + "\n".join(f"  - {p}" for p in created_paths)
    )
    
    log_path.write_text(content)
    return log_path

def main() -> None:
    """Main entry point for directory initialization."""
    print("Starting directory initialization...")
    
    try:
        created = create_directories()
        log_path = write_init_log(created)
        print(f"Success! Created {len(created)} directories.")
        print(f"Log written to: {log_path}")
    except Exception as e:
        print(f"Error during initialization: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
