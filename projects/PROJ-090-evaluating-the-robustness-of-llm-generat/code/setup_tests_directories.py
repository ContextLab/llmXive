import os
import stat
import sys
from pathlib import Path
from typing import List
from config import ensure_directories

def create_test_directories() -> List[str]:
    """
    Create the test directory structure required for the project.
    
    Creates:
    - tests/
    - tests/unit/
    - tests/contract/
    
    Returns:
        List of created directory paths.
    """
    base_dir = Path("tests")
    subdirs = [
        base_dir,
        base_dir / "unit",
        base_dir / "contract",
    ]
    
    created = []
    for dir_path in subdirs:
        # Ensure parent directories exist
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Set permissions to 755 (rwxr-xr-x)
        # os.chmod follows the path, creating it if it doesn't exist? No, mkdir first.
        # We need to set permissions on the existing directory.
        os.chmod(dir_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        
        created.append(str(dir_path))
    
    return created

def verify_directories() -> bool:
    """
    Verify that the test directories exist and have correct permissions (755).
    
    Returns:
        True if all directories exist and have 755 permissions, False otherwise.
    """
    required_dirs = [
        "tests",
        "tests/unit",
        "tests/contract",
    ]
    
    expected_mode = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
    
    all_ok = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            print(f"ERROR: Directory {dir_path} does not exist.")
            all_ok = False
            continue
        
        if not path.is_dir():
            print(f"ERROR: {dir_path} exists but is not a directory.")
            all_ok = False
            continue
        
        current_mode = path.stat().st_mode & 0o777
        if current_mode != expected_mode:
            print(f"ERROR: Directory {dir_path} has permissions {oct(current_mode)}, expected {oct(expected_mode)}")
            all_ok = False
        else:
            print(f"OK: {dir_path} exists with permissions {oct(current_mode)}")
    
    return all_ok

def main():
    """Main entry point for creating test directories."""
    print("Creating test directories...")
    ensure_directories()
    
    created = create_test_directories()
    print(f"Created directories: {created}")
    
    print("\nVerifying directories...")
    if verify_directories():
        print("Verification successful.")
        sys.exit(0)
    else:
        print("Verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()