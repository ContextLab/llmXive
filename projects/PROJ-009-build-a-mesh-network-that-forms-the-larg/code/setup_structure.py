"""
Script to initialize the project directory structure.
This script creates the required directories and __init__.py files
as specified in T001.
"""
import os
from pathlib import Path
from typing import List

def create_structure(base_path: Path) -> List[str]:
    """
    Create the project directory structure.
    
    Args:
        base_path: The root directory for the project (should be 'code/')
        
    Returns:
        List of created directory paths
    """
    directories = [
        "orchestrator",
        "analysis",
        "simulation",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]
    
    created = []
    for dir_name in directories:
        full_path = base_path / dir_name
        full_path.mkdir(parents=True, exist_ok=True)
        created.append(str(full_path))
        
        # Create __init__.py in each directory
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f"# {dir_name} module\n")
    
    return created

def main():
    """Entry point for creating the project structure."""
    # Determine the base path (parent of this script)
    script_path = Path(__file__).parent
    base_path = script_path
    
    print(f"Creating project structure in: {base_path}")
    created_dirs = create_structure(base_path)
    
    print(f"Created {len(created_dirs)} directories:")
    for d in created_dirs:
        print(f"  - {d}")
    
    # Create __init__.py in the root code directory if it doesn't exist
    root_init = base_path / "__init__.py"
    if not root_init.exists():
        root_init.write_text("# Root package for the mesh network supercomputer project\n")
        print(f"Created {root_init}")
        
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()