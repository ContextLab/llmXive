"""
Script to initialize the project directory structure for the llmXive follow-up project.
Creates all required directories for source code, tests, data, and artifacts.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the directory structure to create
    # Using the paths specified in the task description relative to project root
    directories = [
        # Source code structure
        "src/models",
        "src/services",
        "src/cli",
        "src/lib",
        
        # Test structure
        "tests/contract",
        "tests/integration",
        "tests/unit",
        
        # Data structure
        "data/raw",
        "data/processed",
        
        # Artifacts structure
        "artifacts/results",
        "artifacts/plots"
    ]
    
    # Create directories
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure initialization complete.")
    print(f"Created {created_count} new directories.")
    
    # Verify the structure
    print("\nVerifying directory structure:")
    for dir_path in directories:
        full_path = base_dir / dir_path
        status = "✓" if full_path.exists() else "✗"
        print(f"  {status} {dir_path}")

if __name__ == "__main__":
    main()
