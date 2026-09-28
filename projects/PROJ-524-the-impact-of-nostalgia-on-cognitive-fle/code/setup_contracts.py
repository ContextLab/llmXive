import os
import sys
import logging
from pathlib import Path
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp
from config import get_config, ensure_dirs

def create_contracts_directory(config: dict) -> bool:
    """
    Creates the contracts/ directory structure if it does not exist.
    This task (T007) ensures the directory exists for schema files to be generated later.
    """
    contracts_dir = Path(config.get("contracts_dir", "contracts"))
    
    log_info(f"Ensuring contracts directory exists at: {contracts_dir}")
    ensure_dirs([contracts_dir])
    
    if contracts_dir.exists() and contracts_dir.is_dir():
        log_info(f"Contracts directory created/verified: {contracts_dir}")
        return True
    else:
        log_error(f"Failed to create contracts directory: {contracts_dir}")
        return False

def main() -> int:
    """
    Main entry point for T007: Setup contracts directory.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    config = get_config()
    setup_logging()
    
    log_info(f"Starting T007: Setup contracts directory structure at {get_timestamp()}")
    
    success = create_contracts_directory(config)
    
    if success:
        log_info("T007 completed successfully.")
        return 0
    else:
        log_error("T007 failed: Could not create contracts directory.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
