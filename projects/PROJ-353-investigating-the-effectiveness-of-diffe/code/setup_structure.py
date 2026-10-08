"""
Project Structure Initialization Script for llmXive Pipeline.

This script creates the required directory structure for the research project
and verifies that all directories exist before exiting successfully.
"""
import os
import sys
from pathlib import Path

def main():
    """Create project directories and verify their existence."""
    # Define the base project root (current directory)
    project_root = Path(".")
    
    # Define required directory paths relative to project root
    required_dirs = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/analysis",
        "artifacts",
        "contracts",
    ]
    
    created_count = 0
    verified_count = 0
    
    print("Creating project directory structure...")
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        
        # Create directory if it doesn't exist
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"  Created: {full_path}")
        else:
            print(f"  Exists:  {full_path}")
        
        # Verify directory exists
        if full_path.exists() and full_path.is_dir():
            verified_count += 1
        else:
            print(f"  ERROR: Failed to create or verify directory: {full_path}")
            sys.exit(1)
    
    # Final verification summary
    print(f"\nVerification Summary:")
    print(f"  Total directories checked: {len(required_dirs)}")
    print(f"  Directories created:       {created_count}")
    print(f"  Directories verified:      {verified_count}")
    
    if verified_count == len(required_dirs):
        print("\n✓ All required directories exist and are valid.")
        print("Project structure initialization successful.")
        return 0
    else:
        print("\n✗ Verification failed: Some directories are missing.")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
