"""
Task T001b: Set restricted write permissions on data/raw directory.
Executes: chmod 555 data/raw (read-execute only).
"""
import os
import stat
import sys
import logging
from pathlib import Path

# Import existing config constants
try:
    from utils.config import DATA_RAW
except ImportError:
    # Fallback if utils.config is not yet fully populated with DATA_RAW
    # In a real run, this should be defined in config.py
    from pathlib import Path
    DATA_RAW = Path("data/raw")

def set_restricted_permissions():
    """
    Sets the data/raw directory to read-execute only (chmod 555).
    This prevents any writes to the raw data directory, ensuring data integrity.
    """
    target_path = Path(DATA_RAW)
    
    if not target_path.exists():
        logging.error(f"Directory {target_path} does not exist. Run T001a first.")
        return False

    if not target_path.is_dir():
        logging.error(f"{target_path} exists but is not a directory.")
        return False

    # Set permissions to 555 (r-xr-xr-x)
    # 5 = 4 (read) + 1 (execute)
    new_mode = stat.S_IRUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
    
    try:
        os.chmod(target_path, new_mode)
        logging.info(f"Successfully set permissions on {target_path} to 555 (read-execute only).")
        return True
    except PermissionError as e:
        logging.error(f"Permission denied while setting permissions on {target_path}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error setting permissions on {target_path}: {e}")
        return False

def main():
    """Main entry point for T001b."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    success = set_restricted_permissions()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()