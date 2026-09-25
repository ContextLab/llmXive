import os
import sys
import logging
import hashlib
import json
from pathlib import Path

from config import ensure_dirs, get_base_path, get_data_path, get_raw_data_path, get_processed_data_path, get_logs_path

logger = logging.getLogger(__name__)

def create_gitkeep(dir_path: Path) -> None:
    """Create a .gitkeep file in the specified directory to ensure it is tracked by git."""
    gitkeep_path = dir_path / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.touch()
        logger.info(f"Created .gitkeep in {dir_path}")
    else:
        logger.debug(f".gitkeep already exists in {dir_path}")

def setup_data_directories() -> None:
    """
    Create the required project directory structure:
    data/raw, data/processed, data/logs, code, tests, reports, state.
    
    This implements the core requirement of T001.
    """
    base_path = get_base_path()
    
    # Define the directories to create relative to the base path
    # Note: 'code', 'tests', 'reports', 'state' are typically at root level
    # 'data' is a subdirectory containing raw, processed, logs
    
    dirs_to_create = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "logs",
        base_path / "code",
        base_path / "tests",
        base_path / "reports",
        base_path / "state",
    ]

    for dir_path in dirs_to_create:
        ensure_dirs(dir_path)
        logger.info(f"Ensured directory exists: {dir_path}")

        # Create .gitkeep for data subdirectories as per T004 requirements
        if dir_path.parts[-2] == "data" or dir_path.parts[-1] in ["raw", "processed", "logs"]:
            create_gitkeep(dir_path)

def generate_checksums(output_path: Path) -> None:
    """
    Generate checksums for all files in the data directories and save to a JSON file.
    """
    data_path = get_data_path()
    checksums = {}

    for root, _, files in os.walk(data_path):
        for file in files:
            if file.startswith('.'):
                continue
            file_path = Path(root) / file
            try:
                with open(file_path, 'rb') as f:
                  content = f.read()
                  sha256_hash = hashlib.sha256(content).hexdigest()
                  relative_path = file_path.relative_to(data_path)
                  checksums[str(relative_path)] = sha256_hash
                  logger.debug(f"Checksum generated for {relative_path}")
            except Exception as e:
                logger.error(f"Failed to generate checksum for {file_path}: {e}")

    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {output_path}")

def verify_checksums(input_path: Path) -> bool:
    """
    Verify file checksums against a saved JSON file.
    Returns True if all match, False otherwise.
    """
    if not input_path.exists():
        logger.error(f"Checksum file not found: {input_path}")
        return False

    with open(input_path, 'r') as f:
        expected_checksums = json.load(f)

    data_path = get_data_path()
    all_valid = True

    for relative_path_str, expected_hash in expected_checksums.items():
        file_path = data_path / relative_path_str
        if not file_path.exists():
            logger.error(f"File missing during verification: {file_path}")
            all_valid = False
            continue

        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                actual_hash = hashlib.sha256(content).hexdigest()
            
            if actual_hash != expected_hash:
                logger.error(f"Checksum mismatch for {file_path}")
                all_valid = False
            else:
                logger.debug(f"Checksum verified for {file_path}")
        except Exception as e:
            logger.error(f"Error verifying {file_path}: {e}")
            all_valid = False

    return all_valid

def main() -> int:
    """
    Main entry point for the setup script.
    Creates directories and optionally manages checksums.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        logger.info("Starting project directory setup (T001)...")
        setup_data_directories()
        logger.info("Directory structure created successfully.")
        
        # Optional: Generate initial checksums if data exists
        checksum_file = get_base_path() / "data" / ".checksums.json"
        # Only generate if we want to initialize tracking, usually done after data fetch
        # For T001, we just ensure the structure exists.
        
        return 0
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
