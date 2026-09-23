import os
from pathlib import Path

def main():
    """
    Create the required directory structure for the project.
    Implements T001a: data directories
    Implements T001b: source directories
    Implements T001c: test directories
    Implements T005: model cache directory
    """
    # Define all required directories relative to project root
    # Assuming this script is run from the project root or code/ directory
    # We use relative paths to ensure they are created under the project root
    
    # T001a: Data directories
    data_dirs = [
        "data/raw",
        "data/distorted",
        "data/outputs",
        "data/metadata",
        "output/control"
    ]
    
    # T001b: Source directories
    src_dirs = [
        "src/generators",
        "src/inference",
        "src/analysis"
    ]
    
    # T001c: Test directories
    test_dirs = [
        "tests/unit",
        "tests/integration"
    ]
    
    # T005: Model cache directory
    model_dirs = [
        "models"
    ]
    
    all_dirs = data_dirs + src_dirs + test_dirs + model_dirs
    
    created_count = 0
    for dir_path in all_dirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nDirectory creation complete. Created {created_count} new directories.")
    print("Verifying directory structure...")
    
    # Verify all directories exist
    missing = []
    for dir_path in all_dirs:
        path = Path(dir_path)
        if not path.exists() or not path.is_dir():
            missing.append(dir_path)
    
    if missing:
        print(f"ERROR: Missing directories: {missing}")
        return 1
    else:
        print("All required directories verified successfully.")
        return 0

if __name__ == "__main__":
    exit(main())