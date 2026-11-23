import os
import sys
import logging
from pathlib import Path
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp
from config import get_config, ensure_dirs

def create_contracts_directory(base_dir: Path) -> bool:
    """
    Create the contracts/ directory structure if it doesn't exist.
    Returns True if successful, False otherwise.
    """
    contracts_dir = base_dir / "contracts"
    try:
        contracts_dir.mkdir(parents=True, exist_ok=True)
        log_info(f"Created contracts directory: {contracts_dir}")
        return True
    except OSError as e:
        log_error(f"Failed to create contracts directory: {e}")
        return False

def main():
    """
    Main entry point for T007: Setup contracts directory structure.
    """
    # Setup logging
    logger = setup_logging()
    
    # Get configuration
    config = get_config()
    base_dir = config.get("base_dir", Path("."))
    
    log_info("Starting T007: Setup contracts directory structure")
    
    # Create contracts directory
    success = create_contracts_directory(base_dir)
    
    if success:
        log_info("T007 completed successfully")
        return 0
    else:
        log_error("T007 failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
