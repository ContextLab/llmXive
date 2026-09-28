import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import List

# Import shared utilities from existing API surface
try:
    from utils import setup_logger, ensure_directory, PipelineError
except ImportError:
    # Fallback if utils.py is not in path (for standalone execution check)
    def setup_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            logger.addHandler(handler)
        return logger

    def ensure_directory(path: Path):
        path.mkdir(parents=True, exist_ok=True)

    class PipelineError(Exception):
        pass

logger = setup_logger("setup_data_dirs")

REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/logs",
    "code",
    "tests",
    "reports",
    "state"
]

def create_gitkeep(dir_path: Path) -> None:
    """Create a .gitkeep file in the specified directory to ensure it is tracked by git."""
    gitkeep_path = dir_path / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.touch()
        logger.info(f"Created .gitkeep in {dir_path}")
    else:
        logger.debug(f".gitkeep already exists in {dir_path}")

def setup_data_directories(base_path: Path) -> List[Path]:
    """
    Create the required project directory structure.
    
    Args:
        base_path: The root directory of the project.
        
    Returns:
        List of created Path objects.
    """
    created_dirs = []
    for dir_name in REQUIRED_DIRS:
        full_path = base_path / dir_name
        try:
            ensure_directory(full_path)
            create_gitkeep(full_path)
            created_dirs.append(full_path)
            logger.info(f"Ensured directory: {full_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise PipelineError(f"Directory creation failed: {e}")
    return created_dirs

def generate_checksums(base_path: Path, checksum_file: Path) -> None:
    """
    Generate SHA-256 checksums for all .gitkeep files in the data directories.
    This serves as a simple integrity check for the initial structure.
    """
    checksums = {}
    data_dirs = ["data/raw", "data/processed", "data/logs"]
    
    for dir_name in data_dirs:
        dir_path = base_path / dir_name
        gitkeep = dir_path / ".gitkeep"
        if gitkeep.exists():
            with open(gitkeep, "rb") as f:
                content = f.read()
                sha256_hash = hashlib.sha256(content).hexdigest()
                checksums[str(gitkeep.relative_to(base_path))] = sha256_hash
        else:
            logger.warning(f"No .gitkeep found in {dir_path}")
    
    with open(checksum_file, "w") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Generated checksums saved to {checksum_file}")

def verify_checksums(base_path: Path, checksum_file: Path) -> bool:
    """
    Verify the integrity of .gitkeep files against stored checksums.
    """
    if not checksum_file.exists():
        logger.error(f"Checksum file not found: {checksum_file}")
        return False
    
    with open(checksum_file, "r") as f:
        stored_checksums = json.load(f)
    
    all_valid = True
    for rel_path, expected_hash in stored_checksums.items():
        full_path = base_path / rel_path
        if not full_path.exists():
            logger.error(f"File missing for checksum verification: {full_path}")
            all_valid = False
            continue
        
        with open(full_path, "rb") as f:
            current_hash = hashlib.sha256(f.read()).hexdigest()
        
        if current_hash != expected_hash:
            logger.error(f"Checksum mismatch for {full_path}")
            all_valid = False
        else:
            logger.debug(f"Checksum valid for {full_path}")
    
    return all_valid

def main():
    """
    Entry point for the setup script.
    Creates directories, .gitkeep files, and generates initial checksums.
    """
    base_path = Path.cwd()
    logger.info(f"Starting directory setup in {base_path}")
    
    try:
        # 1. Create directories
        setup_data_directories(base_path)
        
        # 2. Generate checksums for the initial state
        checksum_file = base_path / "data" / "structure_checksums.json"
        generate_checksums(base_path, checksum_file)
        
        logger.info("Directory setup completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
