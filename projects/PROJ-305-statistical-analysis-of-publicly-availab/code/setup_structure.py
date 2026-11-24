import os
import subprocess
import logging
from pathlib import Path
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Required directory tree as specified in T001
REQUIRED_DIRS = [
    "src",
    "src/data",
    "src/analysis",
    "src/utils",
    "src/validation",
    "tests",
    "data",
    "data/raw",
    "data/processed",
    "output",
    "output/figures",
    "output/temporal_profiles",
    "contracts",
    "logs",
]

def create_directories() -> None:
    """Create the required project directory tree."""
    logger.info("Creating project directory structure...")
    for dir_path in REQUIRED_DIRS:
        p = Path(dir_path)
        p.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created: {dir_path}")

def _python_tree_fallback(root: Path, max_depth: int = 3) -> List[str]:
    """
    Pure Python implementation of 'tree -a -L 3' for environments 
    where the system 'tree' command is not installed.
    """
    lines = []
    
    def walk(current_path: Path, depth: int):
        if depth > max_depth:
            return
        
        try:
            # Get all entries including hidden ones
            entries = sorted(list(current_path.iterdir()), key=lambda x: x.name)
        except PermissionError:
            return

        for i, entry in enumerate(entries):
            # Simple visual representation
            prefix = "  " * depth + "|-- "
            name = entry.name
            if entry.is_dir():
                name += "/"
            lines.append(f"{prefix}{name}")
            if entry.is_dir():
                walk(entry, depth + 1)

    walk(root, 1)
    return lines

def write_tree_snapshot(root_path: Path, output_file: Path) -> None:
    """
    Capture a filesystem snapshot using the system 'tree' command,
    falling back to a Python implementation if 'tree' is unavailable.
    """
    logger.info(f"Capturing filesystem snapshot to {output_file}...")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Attempt to use the system 'tree' command as requested
        with open(output_file, "w", encoding="utf-8") as f:
            subprocess.run(
                ["tree", "-a", "-L", "3"], 
                cwd=root_path, 
                stdout=f, 
                stderr=subprocess.PIPE, 
                check=True, 
                text=True
            )
        logger.info("Snapshot captured using system 'tree'.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("System 'tree' command not found or failed. Using Python fallback.")
        snapshot = _python_tree_fallback(root_path)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Project Root: {root_path}\n")
            f.write("\n".join(snapshot))
            f.write("\n")
        logger.info("Snapshot captured using Python fallback.")

def main() -> None:
    """Main entry point for project scaffolding."""
    root = Path(".")
    output_file = root / "logs" / "structure.txt"
    
    create_directories()
    write_tree_snapshot(root, output_file)
    
    # Final verification check within the script
    if output_file.exists() and output_file.stat().st_size > 0:
        logger.info("Verification: logs/structure.txt is non-empty.")
    else:
        logger.error("Verification: logs/structure.txt is missing or empty.")
        exit(1)

if __name__ == "__main__":
    main()