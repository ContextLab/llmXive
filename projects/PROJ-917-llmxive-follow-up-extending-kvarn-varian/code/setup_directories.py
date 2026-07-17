import os
import sys
from pathlib import Path

def create_directories(base_path: str = ".") -> None:
    """
    Creates the required directory structure for the llmXive project.
    
    Structure created under `base_path`:
    - data/generated
    - data/models
    - data/simulation
    - data/analysis
    
    Args:
        base_path: The root directory where the structure will be created.
                   Defaults to current working directory.
    """
    root = Path(base_path)
    
    # Define the data subdirectories relative to the root
    data_subdirs = [
        "generated",
        "models",
        "simulation",
        "analysis"
    ]
    
    data_root = root / "data"
    
    # Create the data root if it doesn't exist
    data_root.mkdir(parents=True, exist_ok=True)
    
    # Create each subdirectory
    for subdir in data_subdirs:
        full_path = data_root / subdir
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def verify_structure(base_path: str = ".") -> bool:
    """
    Verifies that the required directory structure exists.
    
    Args:
        base_path: The root directory to check.
        
    Returns:
        True if all required directories exist, False otherwise.
    """
    root = Path(base_path)
    data_root = root / "data"
    
    required_dirs = [
        data_root / "generated",
        data_root / "models",
        data_root / "simulation",
        data_root / "analysis"
    ]
    
    all_exist = True
    for d in required_dirs:
        if not d.is_dir():
            print(f"Missing directory: {d}")
            all_exist = False
        
    return all_exist

def main() -> None:
    """
    Main entry point to create and verify the directory structure.
    """
    print("Creating llmXive data directory structure...")
    create_directories()
    
    if verify_structure():
        print("Directory structure verified successfully.")
        sys.exit(0)
    else:
        print("Directory structure verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()