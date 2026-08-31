"""
Initialize the project directory structure for PROJ-356-predicting-molecular-toxicity-from-struc.

This script programmatically creates the required directory hierarchy to ensure
reproducibility and executability as per FR-001 and Constitution Principles I & V.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Optional

# Define the project root relative to the script location or current working directory
# The task specifies the project is at: projects/PROJ-356-predicting-molecular-toxicity-from-struc/
# We will create the structure relative to the current working directory (CWD)
# The root of the project tree is 'projects/PROJ-356-predicting-molecular-toxicity-from-struc'
# But the task asks for paths like `code/`, `code/src/` etc. relative to the project root.

# Based on the task description, the root of our work is:
# projects/PROJ-356-predicting-molecular-toxicity-from-struc/
# And the subdirectories are:
PROJECT_ROOT_NAME = "PROJ-356-predicting-molecular-toxicity-from-struc"
PARENT_DIR = "projects"

# The specific directories to create under the project root (which is under 'projects/')
# The task lists: code/, code/src/, code/tests/, code/data/, code/data/raw/, code/data/processed/, 
# code/results/, code/models/, code/config/, code/docs/, code/contracts/, code/scripts/, code/state/
# Note: The task description says "create the required directory structure: projects/.../code/..."
# So we create the parent 'projects' dir if needed, then the project dir, then the 'code' tree.

RELATIVE_DIRS = [
    "code",
    "code/src",
    "code/tests",
    "code/data",
    "code/data/raw",
    "code/data/processed",
    "code/results",
    "code/models",
    "code/config",
    "code/docs",
    "code/contracts",
    "code/scripts",
    "code/state",
]

def create_directory_structure(base_path: Path, project_name: str, relative_dirs: List[str]) -> List[Path]:
    """
    Create the directory structure under base_path/project_name.
    
    Args:
        base_path: The parent directory (e.g., 'projects')
        project_name: The name of the project directory
        relative_dirs: List of relative directory paths to create inside the project directory.
        
    Returns:
        List of created Path objects.
    """
    project_root = base_path / project_name
    created_paths = []
    
    # Ensure the project root exists
    project_root.mkdir(parents=True, exist_ok=True)
    created_paths.append(project_root)
    
    for rel_dir in relative_dirs:
        full_path = project_root / rel_dir
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(full_path)
        else:
            # If it exists, we still track it as part of the structure, 
            # but we only 'created' it if we made the call to mkdir.
            # For the purpose of verification, we just ensure it exists.
            pass
            
    return created_paths

def verify_structure(base_path: Path, project_name: str, relative_dirs: List[str]) -> Tuple[bool, List[str]]:
    """
    Verify that all required directories exist.
    
    Args:
        base_path: The parent directory
        project_name: The project directory name
        relative_dirs: List of relative directory paths to check.
        
    Returns:
        Tuple of (is_valid, list_of_missing_dirs)
    """
    project_root = base_path / project_name
    missing_dirs = []
    
    if not project_root.exists():
        return False, [str(project_root)]
        
    for rel_dir in relative_dirs:
        full_path = project_root / rel_dir
        if not full_path.exists():
            missing_dirs.append(str(full_path))
        elif not full_path.is_dir():
            missing_dirs.append(f"{full_path} (exists but is not a directory)")
            
    return len(missing_dirs) == 0, missing_dirs

def main():
    parser = argparse.ArgumentParser(
        description="Initialize the project directory structure for molecular toxicity prediction."
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default=".",
        help="Base directory where the 'projects' folder will be created (default: current directory)"
    )
    parser.add_argument(
        "--project-name",
        type=str,
        default=PROJECT_ROOT_NAME,
        help=f"Name of the project directory (default: {PROJECT_ROOT_NAME})"
    )
    parser.add_argument(
        "--parent-dir",
        type=str,
        default=PARENT_DIR,
        help=f"Name of the parent directory containing the project (default: {PARENT_DIR})"
    )
    
    args = parser.parse_args()
    
    base_path = Path(args.base_dir).resolve()
    parent_dir = Path(args.parent_dir)
    project_name = args.project_name
    
    # Construct the full path to the projects directory
    projects_dir = base_path / parent_dir
    
    print(f"Initializing project structure at: {projects_dir / project_name}")
    
    try:
        # Create directories
        created = create_directory_structure(projects_dir, project_name, RELATIVE_DIRS)
        print(f"Successfully created/verified {len(created)} directories.")
        
        # Verify
        is_valid, missing = verify_structure(projects_dir, project_name, RELATIVE_DIRS)
        
        if not is_valid:
            print("ERROR: The following directories are missing after creation:")
            for m in missing:
                print(f"  - {m}")
            sys.exit(1)
        else:
            print("Verification successful: All required directories exist.")
            
        # List the structure for confirmation
        print("\nCreated structure:")
        for p in sorted(created):
            print(f"  {p.relative_to(base_path)}")
            
    except Exception as e:
        print(f"ERROR: Failed to create directory structure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()