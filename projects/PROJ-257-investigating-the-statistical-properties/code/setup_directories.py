import os
from pathlib import Path

def create_directories():
    """
    Create the src/ directory and its required subdirectories:
    data/, analysis/, viz/, utils/.
    Creates .gitkeep files to ensure git tracks these directories.
    """
    base_dir = Path("src")
    subdirs = ["data", "analysis", "viz", "utils"]

    # Create the main src directory
    base_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / ".gitkeep").touch()

    # Create subdirectories and their .gitkeep files
    for subdir_name in subdirs:
        subdir_path = base_dir / subdir_name
        subdir_path.mkdir(parents=True, exist_ok=True)
        (subdir_path / ".gitkeep").touch()
    
    return base_dir

def main():
    """
    Entry point for directory creation.
    """
    print("Creating src/ directory structure...")
    base_dir = create_directories()
    
    # Verification
    subdirs = ["data", "analysis", "viz", "utils"]
    missing = []
    for subdir in subdirs:
        if not (base_dir / subdir).exists():
            missing.append(subdir)
    
    if missing:
        print(f"ERROR: Missing directories: {missing}")
        return 1
    
    if not (base_dir / ".gitkeep").exists():
        print("ERROR: Missing src/.gitkeep")
        return 1

    print(f"Successfully created directories under {base_dir}:")
    for subdir in subdirs:
        print(f"  - {base_dir / subdir}/")
    print(f"  - {base_dir}/.gitkeep")
    return 0

if __name__ == "__main__":
    exit(main())