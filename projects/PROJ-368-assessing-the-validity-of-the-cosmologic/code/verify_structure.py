"""
Module to verify the project directory structure (Task T004).
Provides verification functionality for the directory structure.
"""
import os
import sys
from pathlib import Path

def verify_structure(base_path: Path = None) -> bool:
    """
    Verifies that the required project directory structure exists.
    
    Args:
        base_path: Base path for the project. Defaults to current working directory.
        
    Returns:
        bool: True if all required directories exist, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    # Define the required directory structure
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/simulations",
        "data/reports",
        "code",
        "tests"
    ]
    
    all_exist = True
    missing_dirs = []
    
    print(f"Verifying directory structure at: {base_path}")
    print("-" * 50)
    
    for dir_path in required_dirs:
        full_path = base_path / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"[OK] {full_path}")
        else:
            print(f"[MISSING] {full_path}")
            missing_dirs.append(dir_path)
            all_exist = False
    
    print("-" * 50)
    
    if all_exist:
        print("✓ All required directories exist.")
        return True
    else:
        print(f"✗ Missing directories: {missing_dirs}")
        return False

def main():
    """Main entry point for structure verification."""
    print("Verifying project directory structure...")
    success = verify_structure()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()