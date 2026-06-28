"""
Manual validation directory structure setup for real-world validation annotations.

This script creates the directory structure required for FR-031b (manual annotation
of real-world A/B test summaries) and verifies all directories exist after creation.

Directory structure created:
- data/manual_validation/
  - raw/           (source URLs and raw HTML)
  - annotations/   (annotator CSV files)
  - processed/     (resolved ground truth and derived artifacts)
  - provenance/    (provenance metadata per Constitution Principle VII)

Exit codes:
- 0: Success (all directories created and verified)
- 1: Failure (directory creation or verification failed)
"""
import sys
from pathlib import Path
from typing import List, Tuple

# Import from existing project modules
from code.src.utils.logger import get_default_logger, AuditLogger

# Define the manual validation directory structure
MANUAL_VALIDATION_DIRS: List[str] = [
    "data/manual_validation",
    "data/manual_validation/raw",
    "data/manual_validation/annotations",
    "data/manual_validation/processed",
    "data/manual_validation/provenance",
]

def create_directory_structure(base_path: Path, dirs: List[str]) -> Tuple[bool, List[Path]]:
    """
    Create directory structure under base_path.
    
    Args:
        base_path: Base project path (should be project root)
        dirs: List of relative directory paths to create
    
    Returns:
        Tuple of (success, list of created paths)
    """
    logger = get_default_logger()
    created_paths: List[Path] = []
    all_success = True
    
    for rel_dir in dirs:
        full_path = base_path / rel_dir
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(full_path)
            logger.info(f"Created directory: {full_path}")
        except OSError as e:
            logger.error(f"ERR-015: Failed to create directory {full_path}: {e}")
            all_success = False
    
    return all_success, created_paths

def verify_directory_structure(base_path: Path, dirs: List[str]) -> Tuple[bool, List[Path]]:
    """
    Verify all directories exist and are accessible.
    
    Args:
        base_path: Base project path
        dirs: List of relative directory paths to verify
    
    Returns:
        Tuple of (all_exist, list of verified paths)
    """
    logger = get_default_logger()
    verified_paths: List[Path] = []
    all_exist = True
    
    for rel_dir in dirs:
        full_path = base_path / rel_dir
        if full_path.exists() and full_path.is_dir():
            verified_paths.append(full_path)
            logger.info(f"Verified directory exists: {full_path}")
        else:
            logger.error(f"ERR-016: Directory missing or not a directory: {full_path}")
            all_exist = False
    
    return all_exist, verified_paths

def main() -> int:
    """
    Main entry point for manual validation directory setup.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Get project root (parent of code/ directory)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent
    
    logger = get_default_logger()
    logger.info("Starting manual validation directory structure setup")
    logger.info(f"Project root: {project_root}")
    
    # Create directory structure
    create_success, created_paths = create_directory_structure(project_root, MANUAL_VALIDATION_DIRS)
    
    if not create_success:
        logger.error("ERR-017: Directory creation failed")
        return 1
    
    # Verify directory structure
    verify_success, verified_paths = verify_directory_structure(project_root, MANUAL_VALIDATION_DIRS)
    
    if not verify_success:
        logger.error("ERR-018: Directory verification failed")
        return 1
    
    logger.info("Manual validation directory structure setup completed successfully")
    logger.info(f"Created {len(verified_paths)} directories")
    return 0

if __name__ == "__main__":
    sys.exit(main())
