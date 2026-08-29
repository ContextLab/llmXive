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
    # Note: data/assets is explicitly included here to ensure it exists,
    # though T004 also mentions it. Creating it here is harmless and ensures
    # the full structure is ready for subsequent tasks.
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
        
        # Verification step as per task requirements
        root = get_project_root()
        required_dirs = [
            "code", "data", "data/synthetic", "data/synthetic/raw",
            "data/synthetic/short_context", "data/results", "data/results/logs",
            "data/results/aggregated", "tests", "models", "data/assets"
        ]
        all_exist = True
        for d in required_dirs:
            if not (root / d).is_dir():
                print(f"ERROR: Directory {d} does not exist!", file=sys.stderr)
                all_exist = False
        
        if all_exist:
            print("Verification passed: All directories exist.")
        else:
            print("Verification failed: Some directories missing.", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error during initialization: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()