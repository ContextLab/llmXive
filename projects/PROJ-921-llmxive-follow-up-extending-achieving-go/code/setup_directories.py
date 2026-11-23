import os
import sys
from pathlib import Path

def setup_data_directories():
    """
    Creates the required directory structure for the project.
    Ensures code/, data/, and tests/ directories and their subdirectories exist.
    """
    root = Path(__file__).resolve().parent.parent
    
    # Define all required directories
    directories = [
        # Code structure
        root / "code" / "data",
        root / "code" / "inference",
        root / "code" / "scoring",
        root / "code" / "analysis",
        root / "code" / "utils",
        
        # Data structure
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "gold",
        
        # Tests structure
        root / "tests" / "unit",
        root / "tests" / "integration",
    ]
    
    created = []
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path.relative_to(root)))
        elif not any(dir_path.iterdir()):
            # Directory exists but is empty, ensure it's recognized
            pass
    
    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All required directories already exist.")
    
    return [str(d.relative_to(root)) for d in directories]

if __name__ == "__main__":
    setup_data_directories()
