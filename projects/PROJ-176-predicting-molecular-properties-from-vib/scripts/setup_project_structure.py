"""
Script to initialize the project directory structure as per T001.
Creates required directories: code/, tests/, data/, specs/, results/, logs/, figures/, state/.
"""
import os
import sys
from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[1]
    
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/preprocessed",
        "data/external",
        "specs",
        "results",
        "logs",
        "figures",
        "state"
    ]

    created = []
    for dir_path in required_dirs:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True)
            created.append(str(full_path.relative_to(root)))
        else:
            # Ensure it's actually a directory
            if not full_path.is_dir():
                print(f"Error: {full_path} exists but is not a directory.")
                sys.exit(1)
    
    # Create __init__.py files for Python packages
    init_files = [
        root / "code" / "__init__.py",
        root / "tests" / "__init__.py"
    ]
    for init_file in init_files:
        if not init_file.exists():
            init_file.write_text('"""Auto-generated package init."""\n')
            created.append(str(init_file.relative_to(root)))

    # Create .gitkeep files to ensure directories are tracked by git
    gitkeep_dirs = [
        "data", "data/raw", "data/preprocessed", "data/external",
        "specs", "results", "logs", "figures", "state"
    ]
    for dir_path in gitkeep_dirs:
        full_path = root / dir_path / ".gitkeep"
        if not full_path.exists():
            full_path.write_text("")
            created.append(str(full_path.relative_to(root)))

    if created:
        print(f"Created {len(created)} directories/files:")
        for item in created:
            print(f"  - {item}")
    else:
        print("Project structure already exists.")

    return 0

if __name__ == "__main__":
    sys.exit(main())