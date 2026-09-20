import os
import stat
import sys
from pathlib import Path

from utils.config import DATA_RAW

logger = logging.getLogger(__name__)


def set_restricted_permissions(path: Path) -> bool:
    """
    Set restricted write permissions (read-execute only: 555) on a directory.
    
    Args:
        path: Path to the directory to restrict.
        
    Returns:
        True if permissions were successfully set, False otherwise.
        
    Raises:
        FileNotFoundError: If the path does not exist.
        PermissionError: If the current user lacks permission to change mode.
    """
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
        
    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")
        
    try:
        # Calculate new mode: remove write bits for user, group, others
        # Current mode | (S_IRUSR | S_IRGRP | S_IROTH | S_IXUSR | S_IXGRP | S_IXOTH)
        # We want to ensure it is 0o555 (r-xr-xr-x)
        current_mode = path.stat().st_mode
        new_mode = current_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
        
        path.chmod(new_mode)
        
        # Verify the change
        final_mode = path.stat().st_mode & 0o777
        expected_mode = 0o555
        
        if final_mode != expected_mode:
            logger.warning(
                f"Permission change resulted in {oct(final_mode)}, "
                f"expected {oct(expected_mode)}. "
                f"This may be due to umask or existing sticky bits."
            )
            # Force exact mode if verification fails
            path.chmod(0o555)
            
        logger.info(f"Successfully set read-execute-only (555) permissions on {path}")
        return True
        
    except PermissionError as e:
        logger.error(f"Permission denied when setting permissions on {path}: {e}")
        raise
    except OSError as e:
        logger.error(f"OS error when setting permissions on {path}: {e}")
        raise


def main():
    """Main entry point for setting restricted permissions on data/raw."""
    import logging
    from utils.logging_setup import get_logger
    
    logger = get_logger(__name__)
    
    try:
        logger.info(f"Attempting to set restricted permissions on {DATA_RAW}")
        set_restricted_permissions(DATA_RAW)
        logger.info("Task T001b completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to set restricted permissions: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
