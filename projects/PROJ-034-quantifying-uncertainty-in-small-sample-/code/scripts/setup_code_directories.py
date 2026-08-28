import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required directory structure for the code/ module.
    Specifically: simulation/, models/, metrics/, validation/, plots/, scripts/
    """
    base_dir = Path(__file__).resolve().parent.parent
    code_dir = base_dir / "code"
    
    subdirectories = [
        "simulation",
        "models",
        "metrics",
        "validation",
        "plots",
        "scripts"
    ]
    
    created_dirs = []
    for subdir in subdirectories:
        dir_path = code_dir / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
        else:
            # Ensure it is a directory
            if not dir_path.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {dir_path}")
    
    return created_dirs

def main():
    """Entry point for script execution."""
    print("Setting up code directory structure...")
    try:
        created = create_directories()
        if created:
            print(f"Created directories: {', '.join(created)}")
        else:
            print("All required directories already exist.")
        
        # Verify existence
        base_dir = Path(__file__).resolve().parent.parent
        code_dir = base_dir / "code"
        expected_subdirs = ["simulation", "models", "metrics", "validation", "plots", "scripts"]
        
        missing = []
        for subdir in expected_subdirs:
            if not (code_dir / subdir).exists():
                missing.append(subdir)
        
        if missing:
            print(f"ERROR: Missing directories after creation attempt: {missing}")
            sys.exit(1)
        else:
            print("Verification successful: All required code subdirectories exist.")
            sys.exit(0)
            
    except Exception as e:
        print(f"ERROR: Failed to create directory structure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()