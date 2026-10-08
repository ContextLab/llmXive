"""
Setup script to create the project directory hierarchy.
Creates code/, data/, tests/, and README.md structure.
"""
import logging
from pathlib import Path

from config import get_project_root, get_data_dir, get_raw_data_dir, get_processed_data_dir
from config import get_consent_dir, get_results_dir, get_figures_dir
from config import get_code_dir, get_tests_dir, get_specs_dir
from logging_config import setup_logging, get_logger


def create_directories():
    """Create the complete project directory hierarchy."""
    logger = get_logger(__name__)
    project_root = get_project_root()
    
    # Core directories
    directories = [
        get_code_dir(),
        get_tests_dir(),
        get_data_dir(),
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir(),
        get_results_dir(),
        get_figures_dir(),
        get_specs_dir(),
    ]
    
    # Additional data subdirectories
    additional_dirs = [
        project_root / "data" / "mock",
        project_root / "data" / "validation",
    ]
    
    all_dirs = directories + additional_dirs
    
    for dir_path in all_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path.relative_to(project_root)}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    for dir_path in all_dirs:
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("")
            logger.debug(f"Created .gitkeep in: {dir_path.relative_to(project_root)}")
    
    return all_dirs


def main():
    """Main entry point for setup script."""
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting project structure setup...")
    
    directories = create_directories()
    
    logger.info(f"Successfully created {len(directories)} directories.")
    logger.info("Project structure setup complete.")
    
    return 0


if __name__ == "__main__":
    exit(main())
