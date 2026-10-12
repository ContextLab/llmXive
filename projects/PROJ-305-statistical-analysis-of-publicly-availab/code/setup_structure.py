import os
import subprocess
import logging
from pathlib import Path
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_directories() -> None:
    """
    Create the required project directory tree as specified in T001.
    """
    required_dirs = [
        "src/data",
        "src/analysis",
        "src/utils",
        "src/validation",
        "tests",
        "data/raw",
        "data/processed",
        "output/figures",
        "output/temporal_profiles",
        "contracts",
        "logs",
    ]
    
    # Also ensure the base src directory exists explicitly
    # although parents=True handles it.
    for d in required_dirs:
        p = Path(d)
        p.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {p}")

def _python_tree_fallback(root: Path, max_depth: int = 3) -> str:
    """
    Pure Python implementation of 'tree -a -L 3' for environments 
    where the system 'tree' command is not installed.
    """
    lines = []
    
    def walk(current_path: Path, depth: int):
        if depth > max_depth:
            return
        
        try:
            # Get all entries including hidden ones (mimic -a)
            entries = sorted(list(current_path.iterdir()), key=lambda x: x.name)
        except PermissionError:
            return

        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            prefix = "└── " if is_last else "├── "
            indent = "    " * depth
            
            # Append the entry name
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{indent}{prefix}{entry.name}{suffix}")
            
            if entry.is_dir():
                walk(entry, depth + 1)

    lines.append(f".")
    walk(root, 0)
    return "\n".join(lines)

def write_tree_snapshot(root_path: Path, output_file: Path) -> None:
    """
    Capture a filesystem snapshot using the system 'tree' command,
    falling back to a Python implementation if 'tree' is unavailable.
    """
    logger.info(f"Capturing filesystem snapshot to {output_file}")
    
    try:
        # Attempt to use the system 'tree' command as requested in T001
        # -a: all files, -L 3: max depth 3
        result = subprocess.run(
            ["tree", "-a", "-L", "3"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        snapshot = result.stdout
        logger.info("Used system 'tree' command for snapshot.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("System 'tree' command not found or failed. Using Python fallback.")
        snapshot = _python_tree_fallback(root_path)

    output_file.write_text(snapshot, encoding="utf-8")
    logger.info(f"Snapshot successfully written to {output_file}")

def main() -> None:
    """
    Main entry point for project scaffolding.
    1. Create the required directory tree.
    2. Write the snapshot to logs/structure.txt.
    """
    root = Path(".")
    
    # 1. Create directories
    create_directories()
    
    # 2. Capture snapshot
    snapshot_path = root / "logs" / "structure.txt"
    write_tree_snapshot(root, snapshot_path)
    
    # Final verification check (mimics the verification step)
    if snapshot_path.exists() and snapshot_path.stat().st_size > 0:
        content = snapshot_path.read_text()
        required_keywords = ["src", "data", "output", "contracts", "logs"]
        all_present = all(kw in content for kw in required_keywords)
        if all_present:
            logger.info("Verification: All required directories found in snapshot.")
        else:
            logger.warning("Verification: Some required directories missing from snapshot.")
    else:
        logger.error("Verification: Snapshot file is missing or empty.")

if __name__ == "__main__":
    main()