import os
from pathlib import Path

def create_project_structure():
    """
    Creates the required project directory structure for the llmXive pipeline.
    
    Creates:
    - code/ (source code)
    - data/raw/ (raw external data)
    - data/processed/ (processed data)
    - data/survey/ (survey responses)
    - tests/ (test suite)
    - docs/ (documentation)
    - config/ (configuration files)
    - figures/ (generated plots)
    
    Ensures all directories exist and are writable.
    """
    # Define the project root (current directory or parent if in a subdirectory)
    # Assuming this script is run from the project root
    project_root = Path.cwd()
    
    # Define required directories relative to project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/survey",
        "data/synth",  # For synthetic data separation (per T026b)
        "tests",
        "tests/unit",
        "tests/integration",
        "docs",
        "config",
        "figures",
        "data/raw/human_coding",  # Per T015c requirement
    ]
    
    created_dirs = []
    skipped_dirs = []
    
    for dir_path in directories:
        full_path = project_root / dir_path
        
        if full_path.exists():
            if full_path.is_dir():
                skipped_dirs.append(dir_path)
            else:
                raise FileExistsError(
                    f"Path exists but is not a directory: {full_path}"
                )
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            # Ensure directory is writable
            if not os.access(full_path, os.W_OK):
                raise PermissionError(
                    f"Cannot write to directory: {full_path}"
                )
    
    # Log results
    if created_dirs:
        print(f"Created directories: {', '.join(created_dirs)}")
    
    if skipped_dirs:
        print(f"Skipped existing directories: {', '.join(skipped_dirs)}")
    
    # Verify final structure
    all_exist = all((project_root / d).is_dir() for d in directories)
    
    if all_exist:
        print("Project structure successfully created/verified.")
        print(f"Root: {project_root}")
        for dir_path in sorted(directories):
            full_path = project_root / dir_path
            print(f"  ✓ {full_path}")
    else:
        missing = [d for d in directories if not (project_root / d).is_dir()]
        raise RuntimeError(f"Failed to create directories: {', '.join(missing)}")
    
    return True

def main():
    """Entry point for command-line execution."""
    try:
        create_project_structure()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
