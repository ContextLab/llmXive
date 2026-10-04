import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates all required data and output directories for the project.
    This function implements T001a and T001b.
    
    Data directories (T001a):
      - data/raw/
      - data/derived/
      - data/derived/topology/
      - data/derived/vdos/
      - data/derived/reference/
      - data/derived/correlation/
      - data/metadata/
      
    Output directories (T001b):
      - outputs/
      - outputs/figures/
      - outputs/reports/
    """
    # Define the project root (assuming scripts/ is at code/scripts/)
    project_root = Path(__file__).resolve().parent.parent
    
    # Define all required directories
    data_dirs = [
        "data/raw",
        "data/derived",
        "data/derived/topology",
        "data/derived/vdos",
        "data/derived/reference",
        "data/derived/correlation",
        "data/metadata",
    ]
    
    output_dirs = [
        "outputs",
        "outputs/figures",
        "outputs/reports",
    ]
    
    all_dirs = [project_root / d for d in data_dirs + output_dirs]
    
    created_count = 0
    for dir_path in all_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nTotal directories created: {created_count}")
    print(f"Total directories checked: {len(all_dirs)}")
    
    # Verify all directories exist
    missing_dirs = [d for d in all_dirs if not d.exists()]
    if missing_dirs:
        print(f"\nERROR: The following directories could not be created:")
        for d in missing_dirs:
            print(f"  - {d}")
        return False
    
    print("\nAll required directories are present.")
    return True

def main():
    """Main entry point for the script."""
    success = create_directories()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()