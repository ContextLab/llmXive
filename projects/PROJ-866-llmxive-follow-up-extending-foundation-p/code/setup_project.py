"""
Project structure initialization script.
Creates the required directory hierarchy for the llmXive research pipeline.
"""
import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the core project directories: code, data, tests, state, contracts.
    Also creates subdirectories for data organization.
    """
    root = Path(__file__).parent.parent
    
    # Core directories
    dirs = [
        root / "code",
        root / "data",
        root / "tests",
        root / "state",
        root / "contracts",
        root / "docs",
        root / "figures",
        
        # Data subdirectories
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        
        # Test subdirectories
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "tests" / "contract",
        
        # Code subdirectories
        root / "code" / "generators",
        root / "code" / "engines",
        root / "code" / "analysis",
        root / "code" / "utils",
        
        # State subdirectories
        root / "state" / "projects",
    ]
    
    created = []
    for dir_path in dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path.relative_to(root)))
        
        # Ensure __init__.py exists in Python packages
        if dir_path.name == "code" or "code" in str(dir_path):
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                created.append(f"{dir_path.relative_to(root)}/__init__.py")
    
    print(f"Created {len(created)} directories/files:")
    for item in sorted(created):
        print(f"  - {item}")
    
    return created

def main():
    """Entry point for script execution."""
    print("Initializing llmXive project structure...")
    create_structure()
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()