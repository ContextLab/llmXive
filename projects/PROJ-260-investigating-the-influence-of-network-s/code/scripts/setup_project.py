"""
Project Structure Initialization Script.

Creates the necessary directory structure for the llmXive research project
according to the implementation plan.

Directories created:
- code/src/: Source code modules
- code/tests/: Test suites
- code/data/: Data artifacts (raw, derived, metadata)
- code/outputs/: Reports and figures
"""
import os
import sys
from pathlib import Path


def create_directories(base_path: str = None) -> dict:
    """
    Create the standard project directory structure.
    
    Args:
        base_path: Optional base path. If None, uses the current working directory.
                   All created directories will be relative to this base.
                   
    Returns:
        dict: Mapping of directory names to their absolute paths.
    """
    if base_path is None:
        base_path = os.getcwd()
    
    base = Path(base_path)
    
    # Define the directory structure relative to the project root
    # Based on tasks.md and standard project organization
    directories = [
        # Source code
        "code/src",
        "code/src/models",
        "code/src/services",
        "code/src/lib",
        "code/src/cli",
        
        # Tests
        "code/tests",
        "code/tests/unit",
        "code/tests/integration",
        "code/tests/contract",
        
        # Data
        "code/data",
        "code/data/raw",
        "code/data/derived",
        "code/data/derived/topology",
        "code/data/derived/vdos",
        "code/data/derived/reference",
        "code/data/derived/correlation",
        "code/data/metadata",
        
        # Outputs
        "code/outputs",
        "code/outputs/reports",
        "code/outputs/figures",
        
        # Scripts
        "code/scripts",
        
        # Specs (feature directory)
        "code/specs",
    ]
    
    created = {}
    for dir_path in directories:
        full_path = base / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created[dir_path] = str(full_path.resolve())
        else:
            created[dir_path] = str(full_path.resolve())
            
    return created


def main():
    """
    Main entry point for the setup script.
    Creates directories and prints a summary of the project structure.
    """
    print("Initializing project structure...")
    
    created_dirs = create_directories()
    
    print(f"Successfully created {len(created_dirs)} directories.")
    print("\nProject structure created:")
    for dir_name, abs_path in sorted(created_dirs.items()):
        print(f"  - {dir_name}")
        
    print("\nProject initialization complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
