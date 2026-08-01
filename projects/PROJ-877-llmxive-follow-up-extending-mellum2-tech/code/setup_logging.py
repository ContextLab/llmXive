import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from config import get_project_root, get_config

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with console and optional file output.
    
    Args:
        name: Logger name
        log_file: Optional file path for log output
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times if logger is reused
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Ensure directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_directory_creation(project_root: Path, subdirs: list, log_file: Optional[str] = None) -> Path:
    """
    Log the creation of project subdirectories.
    
    Args:
        project_root: Path to project root directory
        subdirs: List of subdirectory names relative to project root
        log_file: Optional path to log file
        
    Returns:
        Path to the log file
    """
    logger = setup_logger('directory_setup', log_file)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f"=== Directory Creation Log ===")
    logger.info(f"Timestamp: {timestamp}")
    logger.info(f"Project Root: {project_root}")
    logger.info(f"Subdirectories to create: {', '.join(subdirs)}")
    logger.info("-" * 50)
    
    created_dirs = []
    for subdir in subdirs:
        full_path = project_root / subdir
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            logger.info(f"✓ Created: {full_path}")
        except OSError as e:
            logger.error(f"✗ Failed to create {full_path}: {e}")
    
    logger.info("-" * 50)
    logger.info(f"Total directories created: {len(created_dirs)}")
    logger.info("=== End Directory Creation Log ===")
    
    return Path(log_file) if log_file else project_root / "directory_creation.log"

def main():
    """
    Main function to log directory creation for the project.
    This script is designed to be run to generate the log artifact for T001d.
    """
    project_root = get_project_root()
    
    # Define the subdirectories to be created and logged
    subdirs = [
        "code",
        "data",
        "tests",
        "data/raw",
        "data/processed",
        "data/results"
    ]
    
    # Log file path
    log_file = project_root / "project_subdirs_creation.log"
    
    # Perform logging
    log_path = log_directory_creation(project_root, subdirs, str(log_file))
    
    print(f"Directory creation log written to: {log_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
