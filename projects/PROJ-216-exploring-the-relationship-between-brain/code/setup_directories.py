import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the necessary directory structure for the project.
    Includes data subdirectories, code, tests, and reports.
    """
    base_path = Path(".")
    
    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "interim",
        base_path / "data" / "processed",
        base_path / "code",
        base_path / "tests" / "unit",
        base_path / "tests" / "integration",
        base_path / "reports",
        base_path / "figures",
        base_path / "logs",
    ]
    
    created = []
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        created.append(str(dir_path))
        
    return created

def create_init_files():
    """
    Create __init__.py files in code and tests directories to make them packages.
    """
    base_path = Path(".")
    
    init_paths = [
        base_path / "code" / "__init__.py",
        base_path / "tests" / "__init__.py",
        base_path / "tests" / "unit" / "__init__.py",
        base_path / "tests" / "integration" / "__init__.py",
    ]
    
    created = []
    for init_path in init_paths:
        if not init_path.exists():
            init_path.touch()
            created.append(str(init_path))
        else:
            # Ensure it's not empty if it exists but was previously a placeholder
            # For now, we just ensure the file exists.
            pass
            
    return created

def main():
    """
    Main entry point to set up the project directory structure.
    """
    print("Setting up project directories...")
    
    dirs = create_directories()
    print(f"Created directories: {dirs}")
    
    inits = create_init_files()
    print(f"Created/Verified init files: {inits}")
    
    # Create a placeholder README in reports to satisfy "at least one file" requirement
    reports_dir = Path("reports")
    placeholder = reports_dir / ".gitkeep"
    if not placeholder.exists():
        placeholder.touch()
        print(f"Created placeholder: {placeholder}")
        
    print("Directory setup complete.")

if __name__ == "__main__":
    main()
