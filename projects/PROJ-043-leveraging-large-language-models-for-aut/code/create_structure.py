"""
Script to initialize the project directory structure for PROJ-043.
This script creates all required directories and placeholder __init__.py files
to ensure the project tree is valid and ready for development.
"""
import os
import sys

def create_structure():
    project_root = "projects/PROJ-043-leveraging-large-language-models-for-aut"
    
    required_dirs = [
        # Code subdirectories
        f"{project_root}/code/data",
        f"{project_root}/code/llm",
        f"{project_root}/code/models",
        f"{project_root}/code/utils",
        
        # Data subdirectories
        f"{project_root}/data/raw",
        f"{project_root}/data/processed",
        f"{project_root}/data/cache",
        f"{project_root}/data/results",
        
        # Other top-level directories
        f"{project_root}/tests",
        f"{project_root}/paper",
        f"{project_root}/contracts",
    ]
    
    created_count = 0
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    # Create __init__.py files to make them Python packages
    init_files = []
    for directory in required_dirs:
        init_path = os.path.join(directory, "__init__.py")
        if not os.path.exists(init_path):
            with open(init_path, "w") as f:
                f.write("# Auto-generated package marker for PROJ-043\n")
            init_files.append(init_path)
            print(f"Created __init__.py: {init_path}")
    
    print(f"\nStructure initialization complete. Created {created_count} directories and {len(init_files)} package markers.")
    
    # Verification
    verification_paths = [
        f"{project_root}/code/data",
        f"{project_root}/code/llm",
        f"{project_root}/data/processed",
        f"{project_root}/tests",
        f"{project_root}/paper",
        f"{project_root}/contracts",
    ]
    
    all_exist = True
    for path in verification_paths:
        if not os.path.isdir(path):
            print(f"ERROR: Verification failed - {path} does not exist!")
            all_exist = False
        
    if all_exist:
        print("Verification passed: All required directories exist.")
        return 0
    else:
        print("Verification failed: Some directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(create_structure())