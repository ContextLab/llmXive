"""
Script to initialize the project directory structure.
Creates required folders: code/, tests/, data/, results/, contracts/, state/.
"""
import os
from pathlib import Path

def create_directories():
    """Create the core project directories."""
    root = Path(".")
    dirs = [
        "code",
        "code/utils",
        "code/derived",
        "tests",
        "data",
        "data/raw",
        "data/derived",
        "results",
        "contracts",
        "state",
        "state/projects",
        "figures"
    ]
    
    for d in dirs:
        path = root / d
        if not path.exists():
            path.mkdir(parents=True)
            print(f"Created directory: {path}")
        else:
            print(f"Directory exists: {path}")

def create_init_files():
    """Create __init__.py files to make directories packages."""
    root = Path(".")
    packages = ["code", "tests", "data", "data/raw", "data/derived", "results", "contracts", "state", "state/projects"]
    
    for pkg in packages:
        init_file = root / pkg / "__init__.py"
        if not init_file.exists():
          # Check if it's a sub-package that needs an init or just a folder
          # We only create for logical packages listed above
          with open(init_file, "w") as f:
              f.write(f"# Package: {pkg}\n")
          print(f"Created init file: {init_file}")

def create_gitkeep_files():
    """Create .gitkeep files to ensure empty directories are tracked."""
    root = Path(".")
    keep_dirs = [
        "data/raw",
        "data/derived",
        "results",
        "figures",
        "state/projects"
    ]
    
    for d in keep_dirs:
        path = root / d / ".gitkeep"
        if not path.exists():
            with open(path, "w") as f:
                f.write("# Keep directory\n")
            print(f"Created .gitkeep: {path}")

def main():
    print("Initializing project structure...")
    create_directories()
    create_init_files()
    create_gitkeep_files()
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()