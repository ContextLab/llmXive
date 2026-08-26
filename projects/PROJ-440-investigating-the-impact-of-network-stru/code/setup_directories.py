import os
from pathlib import Path

def setup_directories():
    """
    Create the required directory structure for the project.
    Creates: code/, data/, data/raw/, data/processed/, data/analysis/,
             tests/, contracts/, state/
    """
    base_dir = Path(__file__).resolve().parent.parent
    
    directories = [
        base_dir / "code",
        base_dir / "data",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "analysis",
        base_dir / "tests",
        base_dir / "contracts",
        base_dir / "state",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"Directory setup complete. {created_count} new directories created.")
    return True
