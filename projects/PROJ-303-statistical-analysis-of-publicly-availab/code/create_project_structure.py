"""
Script to create the project directory structure and empty __init__.py files.
This corresponds to task T001.
"""
import os
from pathlib import Path

def main():
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the directory structure relative to the base
    # Based on T001 description: 
    # src/{data,models,evaluation,visualization,pipeline,scripts,cli}
    # tests/{unit,integration,contract}
    # data/{raw,processed}
    # outputs/{plots,metrics}
    # state
    dirs_to_create = [
        # Source directories
        "src/data",
        "src/models",
        "src/evaluation",
        "src/visualization",
        "src/pipeline",
        "src/scripts",
        "src/cli",
        
        # Test directories
        "tests/unit",
        "tests/integration",
        "tests/contract",
        
        # Data directories
        "data/raw",
        "data/processed",
        
        # Output directories
        "outputs/plots",
        "outputs/metrics",
        
        # State directory
        "state"
    ]

    created_dirs = []
    init_files_created = []

    for dir_path in dirs_to_create:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path.relative_to(base_dir)))
        
        # Create __init__.py in all src and tests directories
        if dir_path.startswith("src/") or dir_path.startswith("tests/"):
            init_file = full_path / "__init__.py"
            # Create empty file if it doesn't exist, or touch it
            init_file.touch()
            init_files_created.append(str(init_file.relative_to(base_dir)))

    print(f"Project structure created in: {base_dir}")
    print(f"Directories created: {len(created_dirs)}")
    for d in sorted(created_dirs):
        print(f"  - {d}")
    
    print(f"\n__init__.py files created: {len(init_files_created)}")
    for f in sorted(init_files_created):
        print(f"  - {f}")

if __name__ == "__main__":
    main()