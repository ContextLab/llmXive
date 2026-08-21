"""
Project setup script to create the directory structure for the metallic glass density prediction project.
This script creates all necessary directories as defined in the implementation plan.
"""
import os
from pathlib import Path


def setup_directories():
    """Create the project directory structure."""
    root = Path(__file__).parent.parent
    
    directories = [
        "code/data",
        "code/features",
        "code/models",
        "code/analysis",
        "data",
        "models",
        "reports",
        "tests/unit",
        "tests/contract",
        "tests/integration",
    ]
    
    for dir_path in directories:
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    return True


def main():
    """Main entry point for the setup script."""
    print("Setting up project directory structure...")
    success = setup_directories()
    if success:
        print("Project structure created successfully.")
    else:
        print("Failed to create project structure.")
        exit(1)


if __name__ == "__main__":
    main()
