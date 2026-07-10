import os
import stat
import sys
from pathlib import Path

def set_restricted_permissions():
    """
    Sets restricted write permissions (read-execute only) on the data/raw directory.
    This implements task T001b: chmod 555 data/raw.
    """
    project_root = Path(__file__).resolve().parent.parent
    data_raw_path = project_root / "data" / "raw"

    if not data_raw_path.exists():
        print(f"Error: Directory does not exist: {data_raw_path}")
        print("Please ensure T001a (project structure creation) has been completed.")
        sys.exit(1)

    if not data_raw_path.is_dir():
        print(f"Error: Path exists but is not a directory: {data_raw_path}")
        sys.exit(1)

    try:
        # Set permissions to 555 (r-xr-xr-x)
        # This removes write permissions for owner, group, and others
        os.chmod(data_raw_path, stat.S_IRUSR | stat.S_IXUSR | 
                        stat.S_IRGRP | stat.S_IXGRP | 
                        stat.S_IROTH | stat.S_IXOTH)
        
        # Verify the change
        current_mode = data_raw_path.stat().st_mode
        # Mask to get permission bits only
        perm_bits = current_mode & 0o777
        
        print(f"Successfully set permissions on {data_raw_path}")
        print(f"New permissions: {oct(perm_bits)} (expected: 0o555)")
        
        if perm_bits == 0o555:
            print("Verification passed: Permissions are correctly set to read-execute only.")
            return True
        else:
            print(f"Warning: Permissions verification mismatch. Expected 0o555, got {oct(perm_bits)}")
            return False
            
    except PermissionError as e:
        print(f"Error: Permission denied when attempting to set permissions on {data_raw_path}")
        print(f"Details: {e}")
        print("You may need to run this script with elevated privileges or check directory ownership.")
        return False
    except Exception as e:
        print(f"Unexpected error setting permissions: {e}")
        return False

if __name__ == "__main__":
    success = set_restricted_permissions()
    sys.exit(0 if success else 1)
