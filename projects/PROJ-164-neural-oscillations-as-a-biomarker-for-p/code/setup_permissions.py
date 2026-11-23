import os
import stat
import sys
from pathlib import Path
from utils.config import DATA_RAW

def set_restricted_permissions(path: Path = None):
    """
    Set restricted write permissions (read-execute only) on data/raw.
    Executes: chmod 555 data/raw
    """
    if path is None:
        path = DATA_RAW
    
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    
    # Remove write permissions for owner, group, others
    # 555 = r-xr-xr-x
    current_mode = path.stat().st_mode
    new_mode = current_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    
    os.chmod(path, new_mode)
    
    # Verify
    actual_mode = path.stat().st_mode
    if actual_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH):
        raise PermissionError(f"Failed to set read-only permissions on {path}")
    
    return True

def main():
    """Entry point for setting permissions."""
    try:
        set_restricted_permissions()
        print(f"Permissions set to read-execute only on {DATA_RAW}")
        return 0
    except Exception as e:
        print(f"Error setting permissions: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())