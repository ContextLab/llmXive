"""
Main entry point for the Network Centrality and Neural Synchrony pipeline.

This script initializes the logging infrastructure and sets up the environment
for the research pipeline. It serves as the primary execution point for
orchestrating the various stages of the analysis.

Usage:
    python code/main.py
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime

# Ensure the code directory is in the path for imports if running as script
if __name__ == "__main__":
    code_dir = Path(__file__).parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

from loaders import load_raw_edf, load_annotations
import yaml

# Constants
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
CONFIG_PATH = Path(__file__).parent / "config.yaml"

def setup_logging(log_file: Path) -> logging.Logger:
    """
    Configure the logging infrastructure for the pipeline.
    
    Sets up both file and console handlers with specific formats and levels.
    Ensures the log directory exists before creating the log file.
    
    Args:
        log_file: Path to the log file.
        
    Returns:
        The root logger configured for the pipeline.
    """
    # Create log directory if it doesn't exist
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    try:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except IOError as e:
        print(f"Warning: Could not create log file {log_file}: {e}")
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def load_config() -> dict:
    """
    Load configuration from config.yaml.
    
    Returns:
        Dictionary containing configuration parameters.
        
    Raises:
        FileNotFoundError: If config.yaml is not found.
        yaml.YAMLError: If config.yaml contains invalid YAML.
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
    
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
        
    return config

def validate_dependencies(config: dict) -> bool:
    """
    Validate that required dependencies and configurations are present.
    
    Checks for the existence of required directories and configuration keys.
    
    Args:
        config: Loaded configuration dictionary.
        
    Returns:
        True if all dependencies are valid, False otherwise.
    """
    logger = logging.getLogger(__name__)
    valid = True
    
    # Check required directories
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/metrics",
        "data/results"
    ]
    
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if not full_path.exists():
            logger.warning(f"Required directory missing: {full_path}")
            valid = False
    
    # Check required config keys
    required_keys = [
        "signal_processing",
        "filter_cutoffs",
        "band_definitions"
    ]
    
    for key in required_keys:
        if key not in config:
            logger.warning(f"Missing configuration key: {key}")
            valid = False
    
    return valid

def main():
    """
    Main entry point for the pipeline.
    
    Initializes logging, loads configuration, validates dependencies,
    and sets up the environment for subsequent pipeline stages.
    """
    # Setup logging
    logger = setup_logging(LOG_FILE)
    logger.info("Starting llmXive Network Centrality Pipeline")
    logger.info(f"Log file: {LOG_FILE}")
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Validate dependencies
        logger.info("Validating dependencies...")
        if validate_dependencies(config):
            logger.info("All dependencies validated successfully")
        else:
            logger.warning("Some dependencies are missing or invalid")
        
        logger.info("Pipeline initialization complete")
        
        # Placeholder for future pipeline execution
        # In a full implementation, this would call the download, preprocess,
        # and analysis modules in sequence
        logger.info("Ready to execute pipeline stages")
        
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}")
        sys.exit(1)
    
    logger.info("Pipeline initialization finished successfully")

if __name__ == "__main__":
    main()