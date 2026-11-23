"""
Directory verification module for llmXive project.
Ensures required project directories exist and verifies their state.
"""
import os
import sys
import logging
from pathlib import Path

# Import logging configuration
try:
    from logging_config import setup_logging, get_logger
except ImportError:
    # Fallback if logging_config is not yet available during initial setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    def get_logger(name):
        return logging.getLogger(name)

def ensure_directory(dir_path: str, create_if_missing: bool = True) -> bool:
    """
    Ensure a directory exists. Creates it if missing and create_if_missing is True.
    
    Args:
        dir_path: Relative path from project root
        create_if_missing: Whether to create the directory if it doesn't exist
        
    Returns:
        bool: True if directory exists (or was created), False otherwise
    """
    path = Path(dir_path)
    
    if not path.is_absolute():
        # Assume relative to project root
        path = Path.cwd() / path
        
    logger = get_logger(__name__)
    
    if path.exists():
        if path.is_dir():
            logger.info(f"Directory exists: {path}")
            return True
        else:
            logger.error(f"Path exists but is not a directory: {path}")
            return False
    else:
        if create_if_missing:
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {path}")
                return True
            except OSError as e:
                logger.error(f"Failed to create directory {path}: {e}")
                return False
        else:
            logger.error(f"Directory missing and creation disabled: {path}")
            return False

def main():
    """
    Main function to verify all required directories for the project.
    
    Required directories:
    - data/raw/
    - data/processed/
    - models/
    - reports/
    """
    setup_logging()
    logger = get_logger(__name__)
    
    # Define required directories relative to project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "models",
        "reports"
    ]
    
    logger.info("Starting directory verification for project structure...")
    
    all_success = True
    results = {}
    
    for dir_name in required_dirs:
        success = ensure_directory(dir_name, create_if_missing=True)
        results[dir_name] = {
            "exists": success,
            "path": str(Path(dir_name).resolve())
        }
        if not success:
            all_success = False
    
    # Verify the directories actually exist on disk after creation attempt
    logger.info("\nVerification Results:")
    logger.info("-" * 50)
    
    for dir_name, result in results.items():
        status = "✓" if result["exists"] else "✗"
        logger.info(f"{status} {dir_name}: {result['path']}")
    
    logger.info("-" * 50)
    
    if all_success:
        logger.info("All required directories verified successfully.")
        return 0
    else:
        logger.error("Directory verification failed for one or more directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
