import os
import sys
from pathlib import Path

def verify_t001b_structure(base_path: Path) -> bool:
    """
    Verifies that the required T001b subdirectories exist.
    
    Args:
        base_path: The project root directory (projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/)
        
    Returns:
        True if all required directories exist, False otherwise.
    """
    required_dirs = [
        "src",
        "tests",
        "data"
    ]
    
    all_exist = True
    missing = []
    
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            print(f"MISSING: {dir_path}")
            all_exist = False
            missing.append(dir_name)
        elif not dir_path.is_dir():
            print(f"NOT A DIRECTORY: {dir_path}")
            all_exist = False
            missing.append(dir_name)
        else:
            print(f"OK: {dir_path}")
    
    if missing:
        print(f"Verification failed. Missing directories: {missing}")
        return False
        
    print("Verification passed. All T001b directories exist.")
    return True

def main():
    """Main entry point for T001b verification."""
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
                print(f"Could not locate project code root for verification.")
                sys.exit(1)
    
    print(f"Verifying T001b structure in: {project_code_root}")
    
    if verify_t001b_structure(project_code_root):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
