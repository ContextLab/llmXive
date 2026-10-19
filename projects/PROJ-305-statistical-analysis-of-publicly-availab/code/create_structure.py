import subprocess
import sys
import os
from pathlib import Path
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

REQUIRED_DIRS = [
    "src/data",
    "src/analysis",
    "src/utils",
    "src/validation",
    "tests/unit",
    "tests/integration",
    "tests/fixtures",
    "data/raw",
    "data/processed",
    "data/results",
    "output/figures",
    "output/temporal_profiles",
    "logs",
]

def create_directories():
    """Create all required project directories."""
    for dir_path in REQUIRED_DIRS:
        p = Path(dir_path)
        p.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {dir_path}")

def write_structure_snapshot():
    """
    Capture a three-level directory listing and write to logs/structure.txt.
    Uses 'tree' if available, otherwise falls back to 'find'.
    """
    output_file = paths.logs("structure.txt")
    log.info(f"Writing structure snapshot to {output_file}")
    
    try:
        # Try 'tree' first
        result = subprocess.run(
            ["tree", "-a", "-L", "3"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        output = result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        log.info("Tree command unavailable, falling back to find")
        # Fallback to find . -maxdepth 3 -type d
        result = subprocess.run(
            ["find", ".", "-maxdepth", "3", "-type", "d"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        output = result.stdout

    with output_file.open("w", encoding="utf-8") as f:
        f.write(output)

def main():
    """Main entry point for project scaffolding."""
    create_directories()
    write_structure_snapshot()
    log.info("Project structure established and snapshot recorded.")

if __name__ == "__main__":
    main()
