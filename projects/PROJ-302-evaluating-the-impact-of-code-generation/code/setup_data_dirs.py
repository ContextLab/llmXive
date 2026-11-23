"""
Setup script to create required data subdirectories.
Task: T001b - Create data subdirectories: data/raw/, data/processed/
"""
import os
from pathlib import Path
import sys

def create_data_directories():
    """Create the required data subdirectories."""
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    
    required_dirs = [
        data_dir / "raw",
        data_dir / "processed"
    ]
    
    created = []
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create placeholder .gitkeep files to ensure directories are tracked in git
    for dir_path in required_dirs:
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created placeholder: {gitkeep}")
    
    return created

def main():
    """Main entry point."""
    print("Setting up data directories for T001b...")
    created_dirs = create_data_directories()
    
    if created_dirs:
        print(f"\nSuccessfully created {len(created_dirs)} directories.")
        for d in created_dirs:
            print(f"  - {d}")
    else:
        print("\nAll required directories already existed.")
    
    # Verify final structure
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    print(f"\nFinal data directory structure:")
    for item in sorted(data_dir.rglob("*")):
        rel_path = item.relative_to(base_dir)
        print(f"  {rel_path}")

if __name__ == "__main__":
    main()