"""
Script to create the required project directory structure.
This ensures all necessary folders exist before running the pipeline.
"""
import os
from pathlib import Path
from config import get_project_root, get_raw_data_dir, get_processed_data_dir, get_consent_dir, get_specs_dir, get_contracts_dir, get_figures_dir

def create_directories():
    """Create the full project directory tree."""
    root = get_project_root()
    
    # Core directories
    dirs = [
        root / "code",
        root / "data",
        root / "tests",
        root / "specs",
        # Data subdirectories
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir(),
        root / "data" / "figures", # Ensure figures dir exists if not in config
        # Tests subdirectories
        root / "tests" / "contract",
        root / "tests" / "unit",
        # Specs subdirectories
        get_specs_dir(),
        get_contracts_dir(),
    ]

    created = []
    for d in dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            created.append(str(d.relative_to(root)))
        else:
            # Ensure .gitkeep exists in data folders to keep them tracked
            if "data" in str(d) and d.is_dir():
                gitkeep = d / ".gitkeep"
                if not gitkeep.exists():
                    gitkeep.touch()
                    created.append(f"{str(d.relative_to(root))}/.gitkeep")
    
    # Create .gitkeep in root data folder if needed
    data_root = root / "data"
    if data_root.exists():
        gitkeep = data_root / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            created.append("data/.gitkeep")

    return created

def main():
    """Entry point for CLI."""
    print("Setting up project directory structure...")
    created = create_directories()
    if created:
        print(f"Created directories and files: {', '.join(created)}")
    else:
        print("All directories already exist.")
    
    # Verify structure
    root = get_project_root()
    print(f"\nVerifying structure at {root}:")
    for item in sorted(root.iterdir()):
        print(f"  {item.name}/")

if __name__ == "__main__":
    main()