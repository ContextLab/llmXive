"""
Project Structure Initialization Script.

This script creates the required directory structure for the
Statistical Analysis of Topic Drift in Academic Abstracts project.
"""
import os
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the root directory (current directory)
    root = Path(".")
    
    # Define required directories relative to root
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "results/figures",
        "results/stats",
        "docs"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            skipped_count += 1
    
    print(f"\nProject structure initialization complete.")
    print(f"Created: {created_count}, Skipped (already exist): {skipped_count}")
    
    # Verify structure
    print("\nVerifying directory structure:")
    for dir_path in directories:
        full_path = root / dir_path
        status = "✓" if full_path.exists() else "✗"
        print(f"  {status} {full_path}")

if __name__ == "__main__":
    main()