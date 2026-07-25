import os
import json
import logging
from pathlib import Path
from datetime import datetime
from src.utils.state_manager import save_state, compute_file_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directory_structure(root_path: Path) -> None:
    """
    Create the required directory structure for the project.
    
    Args:
        root_path: The root directory where the structure will be created.
    """
    directories = [
        "data/raw",
        "data/processed",
        "data/artifacts",
        "data/references",
        "state"
    ]
    
    for dir_path in directories:
        full_path = root_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {full_path}")

def log_checksums(root_path: Path) -> None:
    """
    Log checksums of the created directory structure to the state file.
    
    Args:
        root_path: The root directory of the project.
    """
    state_path = root_path / "state"
    checksums = {}
    
    # Log directory hashes
    dirs_to_log = ["data/raw", "data/processed", "data/artifacts", "data/references"]
    for dir_path in dirs_to_log:
        full_path = root_path / dir_path
        if full_path.exists():
          # Since directories are empty initially, we log a placeholder hash or the path itself
          # compute_directory_hash handles empty dirs by hashing the empty structure or returning a specific value
          try:
              h = compute_file_hash(full_path)
              checksums[dir_path] = h
          except Exception as e:
              logger.warning(f"Could not compute hash for {full_path}: {e}")
              checksums[dir_path] = "hash_error"
    
    # Create state entry
    state_entry = {
        "task_id": "T019",
        "timestamp": datetime.now().isoformat(),
        "action": "create_directory_structure",
        "checksums": checksums
    }
    
    # Save to state manager
    save_state(root_path, state_entry)
    logger.info(f"Saved state checksums to {state_path}")

def main():
    """
    Main entry point for the script.
    Creates the data directory structure and logs checksums.
    """
    # Determine project root (assuming script is in code/scripts/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    
    logger.info(f"Project root detected at: {project_root}")
    
    try:
        # Create directory structure
        create_directory_structure(project_root)
        
        # Log checksums to state
        log_checksums(project_root)
        
        logger.info("Task T019 completed successfully.")
        
    except Exception as e:
        logger.error(f"Task T019 failed: {e}")
        raise

if __name__ == "__main__":
    main()
