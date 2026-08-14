import os
import sys
import logging
from pathlib import Path
from utils.logging_config import get_logger

def setup_directories():
    """
    Initialize the project directory structure as defined in T001.
    Creates data/, code/, and tests/ with their respective subdirectories.
    """
    logger = get_logger(__name__)
    project_root = Path(__file__).resolve().parent.parent

    # Define directory structures
    directories = [
        # Data directories
        "data/raw",
        "data/processed",
        "data/outputs",
        "data/config",
        "data/checksums",
        
        # Code directories
        "code/ingestion",
        "code/features",
        "code/models",
        "code/evaluation",
        "code/visualization",
        "code/utils",
        
        # Tests directories
        "tests/contract",
        "tests/integration",
        "tests/unit",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")

    logger.info(f"Directory setup complete. Created {created_count} new directories.")
    return True

def verify_directory_structure():
    """
    Verify that all required directories exist.
    Returns a dictionary with verification results.
    """
    logger = get_logger(__name__)
    project_root = Path(__file__).resolve().parent.parent

    required_dirs = {
        "data": ["raw", "processed", "outputs", "config", "checksums"],
        "code": ["ingestion", "features", "models", "evaluation", "visualization", "utils"],
        "tests": ["contract", "integration", "unit"],
    }

    verification_results = {
        "success": True,
        "missing": [],
        "existing": [],
    }

    for base_dir, sub_dirs in required_dirs.items():
        base_path = project_root / base_dir
        
        # Check base directory
        if not base_path.exists():
            verification_results["success"] = False
            verification_results["missing"].append(str(base_path))
            logger.error(f"Missing base directory: {base_path}")
            continue
        
        verification_results["existing"].append(str(base_path))
        
        # Check subdirectories
        for sub_dir in sub_dirs:
            sub_path = base_path / sub_dir
            if not sub_path.exists():
                verification_results["success"] = False
                verification_results["missing"].append(str(sub_path))
                logger.error(f"Missing subdirectory: {sub_path}")
            else:
                verification_results["existing"].append(str(sub_path))

    return verification_results

def main():
    """
    Main entry point for directory structure setup and verification.
    """
    logger = get_logger(__name__)
    logger.info("Starting project directory structure setup...")

    # Setup directories
    setup_success = setup_directories()
    if not setup_success:
        logger.error("Failed to setup directory structure")
        return 1

    # Verify structure
    verification = verify_directory_structure()
    
    if verification["success"]:
        logger.info("All required directories verified successfully.")
        logger.info(f"Existing directories: {len(verification['existing'])}")
        return 0
    else:
        logger.error(f"Verification failed. Missing directories: {len(verification['missing'])}")
        for missing in verification["missing"]:
            logger.error(f"  - {missing}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
