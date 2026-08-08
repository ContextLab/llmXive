import os
from pathlib import Path
import logging
from typing import List
from .config import get_project_root
from .logging import get_logger

def create_all_directories(project_root: Optional[Path] = None) -> Path:
    """
    Create the full project directory structure including code, data, tests,
    results, and logs with all required subdirectories.
    
    Args:
        project_root: Optional custom project root. If None, uses get_project_root().
        
    Returns:
        Path to the project root.
    """
    if project_root is None:
        project_root = get_project_root()
    
    logger = get_logger(__name__)
    
    # Define all required directories relative to project root
    directories = [
        # Code structure
        "code",
        "code/data",
        "code/models",
        "code/eval",
        "code/utils",
        
        # Data structure
        "data/raw",
        "data/processed",
        "data/splits",
        "data/schemas",
        
        # Tests structure
        "tests/contract",
        "tests/unit",
        "tests/integration",
        
        # Results structure (Task T001d)
        "results/reports",
        "results/plots",
        "results/baseline",
        "results/predictions",
        
        # Logs structure
        "logs",
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
    return project_root

def create_results_directories(project_root: Optional[Path] = None) -> Path:
    """
    Specifically create the results directory structure as required by T001d.
    
    Args:
        project_root: Optional custom project root.
        
    Returns:
        Path to the project root.
    """
    if project_root is None:
        project_root = get_project_root()
        
    logger = get_logger(__name__)
    
    results_dirs = [
        "results",
        "results/reports",
        "results/plots",
        "results/baseline",
        "results/predictions",
    ]
    
    created_count = 0
    for dir_path in results_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created results directory: {full_path}")
            created_count += 1
    
    logger.info(f"Results structure complete. Created {created_count} directories.")
    return project_root

def main():
    """Main entry point for directory creation."""
    import sys
    
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting directory structure creation...")
    
    try:
        project_root = create_all_directories()
        logger.info(f"Successfully created directory structure at: {project_root}")
        
        # Verify results structure specifically for T001d
        results_path = project_root / "results"
        subdirs = ["reports", "plots", "baseline", "predictions"]
        
        for subdir in subdirs:
            path = results_path / subdir
            if not path.exists():
                logger.error(f"Required directory missing: {path}")
                sys.exit(1)
                return
            
        logger.info("All required results directories verified.")
        
    except Exception as e:
        logger.error(f"Failed to create directory structure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
