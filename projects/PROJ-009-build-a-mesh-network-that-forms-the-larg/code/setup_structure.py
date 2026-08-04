"""
Setup script to create the project directory structure for the Mesh Network Supercomputer.
This script creates the required directories as per the implementation plan.
"""
import os
from pathlib import Path

def create_structure():
    """Create the project directory structure."""
    base_dir = Path(__file__).parent.parent
    
    # Define the required directories
    directories = [
        # Code modules
        base_dir / "code" / "orchestrator",
        base_dir / "code" / "orchestrator" / "workers",
        base_dir / "code" / "analysis",
        base_dir / "code" / "simulation",
        base_dir / "code" / "data",
        base_dir / "code" / "data" / "raw",
        base_dir / "code" / "data" / "processed",
        base_dir / "code" / "tests",
        base_dir / "code" / "tests" / "unit",
        base_dir / "code" / "tests" / "integration",
        base_dir / "code" / "tests" / "contract",
        
        # Ensure __init__.py files exist to make them packages
        # (We will create empty ones below)
    ]
    
    # Create directories
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created: {directory}")
    
    # Create __init__.py files to make directories into Python packages
    init_files = [
        base_dir / "code" / "orchestrator" / "__init__.py",
        base_dir / "code" / "orchestrator" / "workers" / "__init__.py",
        base_dir / "code" / "analysis" / "__init__.py",
        base_dir / "code" / "simulation" / "__init__.py",
        base_dir / "code" / "tests" / "__init__.py",
        base_dir / "code" / "tests" / "unit" / "__init__.py",
        base_dir / "code" / "tests" / "integration" / "__init__.py",
        base_dir / "code" / "tests" / "contract" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created: {init_file}")
    
    # Create placeholder files to ensure directories are not empty
    # (Some CI systems or verifiers require non-empty directories)
    placeholder_files = {
        base_dir / "code" / "orchestrator" / ".gitkeep": "Orchestrator module",
        base_dir / "code" / "analysis" / ".gitkeep": "Analysis module",
        base_dir / "code" / "simulation" / ".gitkeep": "Simulation module",
        base_dir / "code" / "data" / "raw" / ".gitkeep": "Raw data storage",
        base_dir / "code" / "data" / "processed" / ".gitkeep": "Processed data storage",
        base_dir / "code" / "tests" / ".gitkeep": "Tests module",
    }
    
    for file_path, content in placeholder_files.items():
        if not file_path.exists():
            file_path.write_text(content)
            print(f"Created placeholder: {file_path}")
    
    print("\nProject structure created successfully!")
    print(f"Base directory: {base_dir}")
    
    # List created structure
    print("\nDirectory structure:")
    for directory in directories:
        if directory.exists():
            print(f"  ✓ {directory.relative_to(base_dir)}")

if __name__ == "__main__":
    create_structure()