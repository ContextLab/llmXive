"""
Project Structure Initialization Script.

This script creates the foundational directory structure required for the
llmXive automated science pipeline. It ensures that all necessary directories
for code, tests, data (raw/processed), figures, and state management exist.
"""
import os
import sys
from pathlib import Path
from typing import List

# Add parent directory to path to allow imports if run as module
# though this script is designed to be run directly from project root
# or code directory.

def get_project_root() -> Path:
    """Determine the project root directory."""
    # If run as main, assume current working directory is project root
    # If run as module, try to find the root based on known structure
    current = Path.cwd()
    
    # Check if we are already in the root (look for 'code' and 'data' adjacent)
    if (current / "code").exists() and (current / "data").exists():
        return current
    
    # Check if we are inside 'code'
    if current.name == "code" and (current.parent / "data").exists():
        return current.parent
    
    # Default to current
    return current

def create_directory_structure(root: Path) -> List[Path]:
    """
    Create the standard project directory structure.
    
    Args:
        root: The project root directory path.
        
    Returns:
        A list of created directory paths.
    """
    directories = [
        # Core infrastructure
        root / "code",
        root / "code" / "data",
        root / "code" / "utils",
        root / "code" / "setup",
        
        # Testing
        root / "tests",
        root / "tests" / "contract",
        
        # Data management
        root / "data",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "external", # For downloaded external data if needed
        
        # Outputs
        root / "figures",
        
        # State and Specs
        root / "state",
        root / "state" / "projects",
        root / "specs",
        root / "specs" / "001-molecular-flexibility-permeability",
        root / "specs" / "001-molecular-flexibility-permeability" / "contracts",
        
        # Logs
        root / "logs",
    ]
    
    created = []
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory exists: {dir_path}")
            
    return created

def main():
    """Main entry point for the script."""
    print("Initializing project structure...")
    root = get_project_root()
    print(f"Project root detected at: {root}")
    
    created_dirs = create_directory_structure(root)
    
    if created_dirs:
        print(f"\nSuccessfully created {len(created_dirs)} directories.")
    else:
        print("\nNo new directories created. Structure already exists.")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
