import os
import sys
from pathlib import Path

def create_directory_structure(base_path: str) -> bool:
    """
    Creates the required directory structure for the project.
    
    Args:
        base_path: The root directory where the project structure will be created.
        
    Returns:
        True if all directories were created successfully, False otherwise.
    """
    project_root = Path(base_path)
    
    # Define all required directories relative to project root
    directories = [
        "code",
        "data",
        "state",
        "tests",
        "docs",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "state/projects",
        "tools",
        "reviews"
    ]
    
    success = True
    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
        except OSError as e:
            print(f"ERROR: Failed to create directory {full_path}: {e}")
            success = False
    
    return success

def write_setup_log(base_path: str, success: bool) -> str:
    """
    Writes the setup log file indicating the result of directory creation.
    
    Args:
        base_path: The root directory where the log file will be written.
        success: Boolean indicating if directory creation was successful.
        
    Returns:
        Path to the created log file.
    """
    log_path = Path(base_path) / "setup_log.txt"
    status = "SUCCESS" if success else "FAILED"
    timestamp = __import__('datetime').datetime.now().isoformat()
    
    content = f"""Project Directory Initialization Log
=====================================
Timestamp: {timestamp}
Status: {status}
Project Root: {base_path}

Directories Created:
- code/
- data/
- state/
- tests/
- docs/
- data/raw/
- data/processed/
- tests/unit/
- tests/integration/
- state/projects/
- tools/
- reviews/

Verification:
All required directories were {'successfully' if success else 'NOT successfully'} created.
"""
    
    with open(log_path, 'w') as f:
        f.write(content)
        
    print(f"Setup log written to: {log_path}")
    return str(log_path)

def main():
    """Main entry point for project initialization."""
    # Determine project root based on task description
    # The task specifies creating directories in: projects/PROJ-308-quantifying-entanglement-entropy-in-rand/
    base_path = Path("projects/PROJ-308-quantifying-entanglement-entropy-in-rand")
    
    print(f"Initializing project structure at: {base_path}")
    
    if not create_directory_structure(str(base_path)):
        write_setup_log(str(base_path), False)
        sys.exit(1)
    
    write_setup_log(str(base_path), True)
    print("Project initialization complete.")

if __name__ == "__main__":
    main()