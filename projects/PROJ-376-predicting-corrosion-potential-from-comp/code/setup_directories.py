import os
import sys
import json
from pathlib import Path
from datetime import datetime
from utils.logging import get_logger

# Ensure we can import utils if run as a script from code/
if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    if script_dir not in sys.path:
        sys.path.insert(0, str(script_dir))

logger = get_logger(__name__)

REQUIRED_DIRS = [
    "code",
    "data",
    "data/raw",
    "data/processed",
    "data/logs",
    "state",
    "contracts",
    "config",
    "code/data",
    "code/models",
    "code/utils",
    "code/tests",
]

def create_directories(root_dir: Path) -> list:
    """
    Creates all required directories under root_dir.
    Returns a list of dicts: {"path": "<absolute_path>", "created_at": "<ISO8601>"}
    """
    results = []
    for rel_path in REQUIRED_DIRS:
        target_path = root_dir / rel_path
        # Ensure parent exists (though our list is flat enough, good practice)
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Record creation/modification time (use mtime if exist, else now)
        # Since we might be re-running, we log the current state timestamp for verification
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        results.append({
            "path": str(target_path.resolve()),
            "created_at": timestamp
        })
        logger.info(f"Ensured directory exists: {target_path}")
    
    return results

def verify_directories(root_dir: Path, created_dirs: list) -> bool:
    """
    Verifies that all directories listed in created_dirs actually exist on disk.
    Returns True if all exist, False otherwise.
    """
    all_exist = True
    for item in created_dirs:
        p = Path(item["path"])
        if not p.exists() or not p.is_dir():
            logger.error(f"Verification failed: Directory does not exist: {p}")
            all_exist = False
    return all_exist

def main():
    # Determine project root (parent of code/)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent 
    
    logger.info(f"Project root identified as: {project_root}")
    
    # Create directories
    created_dirs = create_directories(project_root)
    
    # Verify
    if verify_directories(project_root, created_dirs):
        logger.info("All directories verified successfully.")
        
        # Write verification JSON
        verification_file = project_root / "state" / "setup_dirs_verified.json"
        with open(verification_file, "w") as f:
            json.dump(created_dirs, f, indent=2)
        
        logger.info(f"Verification report written to: {verification_file}")
        return 0
    else:
        logger.error("Directory verification failed. Some directories missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
