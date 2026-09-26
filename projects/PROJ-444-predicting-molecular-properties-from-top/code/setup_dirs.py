"""
T001 Implementation: Create project structure per implementation plan.

This script initializes the directory structure required for the
PROJ-444-predicting-molecular-properties-from-top project, ensuring
all necessary folders for data, logs, state, and reports exist.
"""
import os
import sys
from pathlib import Path

# Define the project root relative to the script location or current working directory
# The task requires paths relative to the project root.
# We assume the script is run from the project root or the root is the parent of 'code'.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "PROJ-444-predicting-molecular-properties-from-top"

# Define the required directory structure
# Based on tasks.md and standard research pipeline conventions
REQUIRED_DIRS = [
    # Data directories
    "data/raw",
    "data/processed",
    "data/logs",
    "data/figures",
    
    # State tracking (Constitution III compliance)
    "state",
    f"state/projects/{PROJECT_NAME}",
    
    # Reports directory
    "reports",
    "reports/metrics",
    "reports/plots",
    
    # Documentation (if not already present)
    "docs",
    
    # Tests directory
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
]

def ensure_directory(dir_path: Path) -> bool:
    """
    Ensure a directory exists. Create it if it does not.
    
    Args:
        dir_path: Path object representing the directory to create.
        
    Returns:
        True if the directory was created or already existed, False on failure.
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Directory created/exists: {dir_path}")
        return True
    except OSError as e:
        print(f"[ERROR] Failed to create directory {dir_path}: {e}")
        return False

def initialize_state_file(project_state_path: Path) -> bool:
    """
    Initialize the project state YAML file if it doesn't exist.
    This satisfies the requirement for state tracking in Constitution III.
    
    Args:
        project_state_path: Path to the state YAML file.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        if not project_state_path.exists():
          # Initialize with a basic structure
          content = """project_id: PROJ-444-predicting-molecular-properties-from-top
status: initialized
created_at: """ + str(Path().cwd()) + """
artifacts: {}
checksums: {}
"""
          with open(project_state_path, "w", encoding="utf-8") as f:
              f.write(content)
          print(f"[OK] Initialized state file: {project_state_path}")
        else:
          print(f"[OK] State file already exists: {project_state_path}")
        return True
    except IOError as e:
        print(f"[ERROR] Failed to initialize state file {project_state_path}: {e}")
        return False

def main():
    """
    Main entry point for the setup script.
    Creates all required directories and initializes state tracking.
    """
    print(f"Setting up project structure for: {PROJECT_NAME}")
    print(f"Project Root: {PROJECT_ROOT}")
    
    success = True
    
    # Create all required directories
    for dir_str in REQUIRED_DIRS:
        dir_path = PROJECT_ROOT / dir_str
        if not ensure_directory(dir_path):
            success = False
    
    # Initialize the specific project state file
    state_file_path = PROJECT_ROOT / "state" / "projects" / PROJECT_NAME / "project_state.yaml"
    if not initialize_state_file(state_file_path):
        success = False
    
    if success:
        print("\n[SUCCESS] Project structure initialized successfully.")
        sys.exit(0)
    else:
        print("\n[FAILURE] Some directories or files could not be created.")
        sys.exit(1)

if __name__ == "__main__":
    main()