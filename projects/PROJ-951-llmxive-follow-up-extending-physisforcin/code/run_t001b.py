import os
import sys
from pathlib import Path
from create_t001b_directories import create_t001b_directories
from verify_t001b_structure import verify_t001b_structure

def main():
    """
    Orchestrates the creation and verification of T001b directories.
    """
    current_dir = Path.cwd()
    script_dir = Path(__file__).parent
    
    # Attempt to locate the project code root
    project_code_root = current_dir / "projects" / "PROJ-951-llmxive-follow-up-extending-physisforcin" / "code"
    
    if not project_code_root.exists():
        project_code_root = script_dir / "projects" / "PROJ-951-llmxive-follow-up-extending-physisforcin" / "code"
        
        if not project_code_root.exists():
            if (script_dir / "projects").exists():
                project_code_root = script_dir
            else:
                print("Error: Could not locate project code root.")
                sys.exit(1)
    
    print(f"Executing T001b in: {project_code_root}")
    
    # Step 1: Create directories
    print("--- Creating directories ---")
    if not create_t001b_directories(project_code_root):
        print("Error: Directory creation failed.")
        sys.exit(1)
        
    # Step 2: Verify structure
    print("--- Verifying structure ---")
    if not verify_t001b_structure(project_code_root):
        print("Error: Structure verification failed.")
        sys.exit(1)
        
    print("T001b execution completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
