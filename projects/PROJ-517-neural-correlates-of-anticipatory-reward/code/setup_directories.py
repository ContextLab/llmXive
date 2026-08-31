import os
from pathlib import Path

def main():
    """
    Creates the required data directory structure for the project.
    This script ensures the existence of:
    - data/raw/
    - data/processed/
    - data/figures/
    
    It also creates a .gitkeep file in each to ensure they are tracked by git
    even if empty.
    """
    project_root = Path(__file__).parent.parent
    data_root = project_root / "data"
    
    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "figures"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directory is tracked
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Keep directory\n")
        print(f"Created/Verified: {directory}")

    print("Data directory structure setup complete.")

if __name__ == "__main__":
    main()
