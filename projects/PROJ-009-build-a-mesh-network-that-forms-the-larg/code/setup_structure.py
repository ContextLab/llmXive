"""
Project structure setup script for the Mesh Network Supercomputer project.
Creates the necessary directory hierarchy as per the implementation plan.
"""
import os
from pathlib import Path

def create_structure():
    """Create the project directory structure."""
    root = Path(".")
    
    # Define all required directories
    directories = [
        # Code modules
        "code/orchestrator/workers",
        "code/analysis",
        "code/simulation",
        
        # Data directories
        "data/raw",
        "data/processed",
        
        # Test directories
        "tests/contract",
        "tests/integration",
        "tests/unit",
        
        # Specs directory (if not exists)
        "specs/001-mesh-supercomputer",
        
        # Contracts directory for schemas
        "contracts",
        
        # State directory for runtime state
        "state",
        
        # Figures directory for plots
        "figures",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory exists: {full_path}")
    
    # Create __init__.py files for Python packages
    package_dirs = [
        "code",
        "code/orchestrator",
        "code/orchestrator/workers",
        "code/analysis",
        "code/simulation",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
    ]
    
    for pkg_dir in package_dirs:
        init_file = root / pkg_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created package marker: {init_file}")
        
    print(f"\nProject structure setup complete. Created {created_count} new directories.")
    return created_count

if __name__ == "__main__":
    create_structure()
