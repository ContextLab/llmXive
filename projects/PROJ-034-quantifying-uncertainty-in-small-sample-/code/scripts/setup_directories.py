"""
Script to setup the project directory structure for the llmXive research pipeline.
Creates necessary directories under code/, data/, tests/, and docs/ as defined in T001.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the required directory structure."""
    base_path = Path(__file__).resolve().parent.parent.parent
    
    # Define all required directories relative to the project root
    directories = [
        "code/simulation",
        "code/models",
        "code/metrics",
        "code/validation",
        "code/plots",
        "code/scripts",
        "data/raw",
        "data/simulated",
        "data/results",
        "tests/unit",
        "tests/integration",
        "docs/paper"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create .gitkeep files in data directories to ensure they are tracked by git
    data_dirs = ["data/raw", "data/simulated", "data/results"]
    for dir_path in data_dirs:
        full_path = base_path / dir_path / ".gitkeep"
        if not full_path.exists():
            full_path.touch()
            print(f"Created .gitkeep in: {full_path.parent}")
    
    print(f"\nDirectory setup complete. Created {created_count} new directories.")
    return True

def main():
    """Main entry point for the script."""
    print("Setting up project directory structure...")
    try:
        create_directories()
        print("Setup completed successfully.")
        return 0
    except Exception as e:
        print(f"Error during setup: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())