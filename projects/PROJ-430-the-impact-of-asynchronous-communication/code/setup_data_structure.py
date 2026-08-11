"""
Setup script for data directory structure.

Creates the required subdirectories under data/ (raw, derived, validation, logs)
and configures .gitignore rules to exclude generated data files while keeping
.gitkeep files for empty directories.
"""
import os
import sys
from pathlib import Path
from config import get_config, ensure_directories_exist
from utils.logger import get_logger, log_pipeline_start, log_pipeline_complete

def setup_data_structure():
    """
    Create the data directory structure with appropriate .gitignore rules.
    
    Creates:
    - data/raw/ (for raw fetched data)
    - data/derived/ (for processed data)
    - data/validation/ (for validation datasets)
    - data/logs/ (for pipeline logs)
    
    Configures .gitignore to:
    - Exclude *.csv and *.json in raw/
    - Keep .gitkeep in validation/
    """
    logger = get_logger(__name__)
    config = get_config()
    data_dir = config.get('data_dir', Path('data'))
    
    logger.info("Setting up data directory structure...")
    
    # Define subdirectories
    subdirs = [
        'raw',
        'derived',
        'validation',
        'logs'
    ]
    
    # Create directories
    for subdir in subdirs:
        dir_path = data_dir / subdir
        ensure_directories_exist([dir_path], logger)
        logger.info(f"Created directory: {dir_path}")
    
    # Create .gitkeep in validation directory to ensure it's tracked even when empty
    validation_dir = data_dir / 'validation'
    gitkeep_path = validation_dir / '.gitkeep'
    if not gitkeep_path.exists():
        gitkeep_path.touch()
        logger.info(f"Created .gitkeep file in {validation_dir}")
    
    # Create .gitignore in raw directory to exclude generated files
    raw_dir = data_dir / 'raw'
    gitignore_path = raw_dir / '.gitignore'
    if not gitignore_path.exists():
        gitignore_content = """# Exclude generated data files
*.csv
*.json
*.parquet
*.log
"""
        gitignore_path.write_text(gitignore_content)
        logger.info(f"Created .gitignore in {raw_dir} to exclude generated files")
    
    # Create .gitignore in derived directory
    derived_dir = data_dir / 'derived'
    derived_gitignore_path = derived_dir / '.gitignore'
    if not derived_gitignore_path.exists():
        derived_gitignore_content = """# Exclude generated derived data files
*.csv
*.json
*.parquet
"""
        derived_gitignore_path.write_text(derived_gitignore_content)
        logger.info(f"Created .gitignore in {derived_dir}")
    
    # Create .gitignore in logs directory
    logs_dir = data_dir / 'logs'
    logs_gitignore_path = logs_dir / '.gitignore'
    if not logs_gitignore_path.exists():
        logs_gitignore_content = """# Exclude log files
*.log
*.json
"""
        logs_gitignore_path.write_text(logs_gitignore_content)
        logger.info(f"Created .gitignore in {logs_dir}")
    
    logger.info("Data directory structure setup complete.")
    return True

def main():
    """Main entry point for the setup script."""
    log_pipeline_start("setup_data_structure")
    try:
        success = setup_data_structure()
        if success:
            log_pipeline_complete("setup_data_structure")
            print("Data directory structure setup completed successfully.")
            return 0
        else:
            print("Failed to setup data directory structure.")
            return 1
    except Exception as e:
        log_pipeline_error("setup_data_structure", str(e))
        print(f"Error during setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())