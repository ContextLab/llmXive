"""
Script to create essential placeholder files for the project.

This ensures that the project structure is not only directories
but also contains the necessary __init__.py files and basic
configuration placeholders.
"""
import os
import sys
from pathlib import Path


def create_placeholder_files(base_path: str = None) -> list:
    """
    Create __init__.py files and other necessary placeholders.
    
    Args:
        base_path: Optional base path. Defaults to current working directory.
                    
    Returns:
        list: List of created file paths.
    """
    if base_path is None:
        base_path = os.getcwd()
    
    base = Path(base_path)
    
    # Define files to create
    files_to_create = [
        # Source __init__.py files
        "code/src/__init__.py",
        "code/src/models/__init__.py",
        "code/src/services/__init__.py",
        "code/src/lib/__init__.py",
        "code/src/cli/__init__.py",
        
        # Test __init__.py files
        "code/tests/__init__.py",
        "code/tests/unit/__init__.py",
        "code/tests/integration/__init__.py",
        "code/tests/contract/__init__.py",
        
        # Data __init__.py files
        "code/data/__init__.py",
        
        # Output __init__.py files
        "code/outputs/__init__.py",
        
        # Scripts __init__.py file
        "code/scripts/__init__.py",
        
        # Specs __init__.py file
        "code/specs/__init__.py",
    ]
    
    created_files = []
    for file_path in files_to_create:
        full_path = base / file_path
        if not full_path.exists():
            full_path.touch()
            # Add a docstring to __init__.py files
            if file_path.endswith("__init__.py"):
                with open(full_path, 'w') as f:
                    f.write(f'"""Package initialization for {file_path}."""\n')
            created_files.append(str(full_path.resolve()))
        else:
            created_files.append(str(full_path.resolve()))
            
    return created_files


def main():
    """
    Main entry point for creating placeholder files.
    """
    print("Creating placeholder files...")
    
    created_files = create_placeholder_files()
    
    print(f"Successfully created {len(created_files)} placeholder files.")
    print("\nFiles created:")
    for file_path in sorted(created_files):
        print(f"  - {file_path}")
        
    print("\nPlaceholder file creation complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())