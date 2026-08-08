import os
import stat
import sys
from pathlib import Path

def set_restricted_permissions(target_path: str) -> bool:
    """
    Sets restricted read-execute only permissions (555) on the target directory.
    
    This implements T001b: Set restricted write permissions on `data/raw`.
    
    Args:
        target_path: Relative or absolute path to the directory (e.g., 'data/raw')
        
    Returns:
        True if permissions were successfully set, False otherwise.
        
    Raises:
        FileNotFoundError: If the target path does not exist.
        PermissionError: If the current user cannot modify permissions.
    """
    path = Path(target_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Target path does not exist: {path}")
    
    if not path.is_dir():
        raise NotADirectoryError(f"Target path is not a directory: {path}")
    
    # Calculate new mode: Read (4) + Execute (1) for Owner, Group, Others = 555
    # This removes write (2) permissions for all.
    new_mode = stat.S_IRUSR | stat.S_IXUSR | \
               stat.S_IRGRP | stat.S_IXGRP | \
               stat.S_IROTH | stat.S_IXOTH
    
    try:
        # Apply the mode
        os.chmod(path, new_mode)
        
        # Verify the change
        current_mode = path.stat().st_mode
        # Mask out file type bits to compare just permission bits
        perm_bits = current_mode & 0o777
        
        if perm_bits != new_mode:
            raise PermissionError(
                f"Failed to set permissions. Expected 555, got {oct(perm_bits)}"
            )
        
        return True
        
    except OSError as e:
        raise PermissionError(f"Failed to change permissions on {path}: {e}") from e

def main():
    """Entry point for the permission setting script."""
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    target = "data/raw"
    
    try:
        success = set_restricted_permissions(target)
        if success:
            logging.info(f"Successfully set read-execute only permissions (555) on {target}")
            # Verify and log the actual result
            import stat
            actual_mode = os.stat(target).st_mode & 0o777
            logging.info(f"Verified permissions on {target}: {oct(actual_mode)}")
            sys.exit(0)
        else:
            logging.error(f"Failed to set permissions on {target}")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Error setting permissions: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
