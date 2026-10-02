import os
import sys
from pathlib import Path

def verify_directories(base_path: str) -> bool:
    """
    Verifies that all required directories exist.
    
    Args:
        base_path: The root directory to verify.
        
    Returns:
        True if all directories exist, False otherwise.
    """
    required_dirs = [
        "code",
        "data",
        "state",
        "tests",
        "docs",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "state/projects",
        "tools",
        "reviews"
    ]
    
    all_exist = True
    missing = []
    
    for dir_path in required_dirs:
        full_path = Path(base_path) / dir_path
        if not full_path.exists():
            print(f"MISSING: {full_path}")
            missing.append(dir_path)
            all_exist = False
        elif not full_path.is_dir():
            print(f"NOT A DIRECTORY: {full_path}")
            missing.append(dir_path)
            all_exist = False
        else:
            print(f"OK: {full_path}")
    
    return all_exist

def main():
    """Main verification entry point."""
    base_path = "projects/PROJ-308-quantifying-entanglement-entropy-in-rand"
    
    print(f"Verifying directory structure at: {base_path}")
    
    if not Path(base_path).exists():
        print(f"ERROR: Base path does not exist: {base_path}")
        sys.exit(1)
    
    success = verify_directories(base_path)
    
    if success:
        print("\nVerification PASSED: All required directories exist.")
        sys.exit(0)
    else:
        print("\nVerification FAILED: Some directories are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()