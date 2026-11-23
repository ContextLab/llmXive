"""
Setup script to create the complete project directory structure.
This script ensures all required directories for the llmXive project exist.
"""
import os
from pathlib import Path


def create_directory_structure():
    """Create all required directories for the project."""
    root = Path("projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v")

    # Core project directories
    dirs = [
        # Code structure
        root / "code",
        root / "code" / "analysis",
        root / "code" / "data",
        root / "code" / "data" / "cache",
        root / "code" / "models",
        root / "code" / "utils",
        root / "code" / "src" / "analysis",
        root / "code" / "src" / "data",
        root / "code" / "src" / "models",
        root / "code" / "src" / "utils",
        
        # Test structure
        root / "tests",
        root / "tests" / "unit",
        root / "tests" / "integration",
        
        # Data structure
        root / "data",
        root / "data" / "raw",
        root / "data" / "interim",
        root / "data" / "results",
        root / "data" / "manual",
        
        # Specs structure
        root / "specs",
        root / "specs" / "001-llmxive-vae-geometric-analysis",
        
        # Contracts structure
        root / "contracts",
    ]

    created_count = 0
    for dir_path in dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created: {dir_path}")
        else:
            print(f"Exists: {dir_path}")

    print(f"\nTotal directories created: {created_count}")
    print(f"Project root: {root.absolute()}")
    return created_count


def main():
    """Entry point for the setup script."""
    print("=" * 60)
    print("llmXive Project Directory Structure Setup")
    print("Project: PROJ-810-llmxive-follow-up-extending-qwen-image-v")
    print("=" * 60)
    
    created = create_directory_structure()
    
    if created >= 0:
        print("\n✅ Directory structure setup complete.")
    else:
        print("\n❌ Directory structure setup failed.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())