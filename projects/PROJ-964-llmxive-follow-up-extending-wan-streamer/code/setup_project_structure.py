import os
from pathlib import Path

def create_directory_structure():
    """
    Orchestrates the creation of all required project directories.
    """
    from code.setup_directories import setup_code_directories
    from code.setup_data_directories import setup_data_directories
    from code.setup_state_docs import setup_state_docs_directories
    from code.setup_project_root import setup_project_root
    
    print("Creating full project directory structure...")
    
    code_dirs = setup_code_directories()
    data_dirs = setup_data_directories()
    state_docs_dirs = setup_state_docs_directories()
    project_root = setup_project_root()
    
    return {
        "code": code_dirs,
        "data": data_dirs,
        "state_docs": state_docs_dirs,
        "project_root": project_root
    }

def verify_full_structure():
    """
    Verifies the entire project structure.
    """
    from code.setup_directories import verify_directories as verify_code
    from code.setup_data_directories import verify_data_directories as verify_data
    from code.setup_state_docs import verify_state_docs_directories as verify_state_docs
    from code.setup_project_root import verify_project_root as verify_root
    
    print("Verifying full project structure...")
    
    code_ok = verify_code()
    data_ok = verify_data()
    state_docs_ok = verify_state_docs()
    root_ok = verify_root()
    
    return code_ok and data_ok and state_docs_ok and root_ok

def main():
    """
    Main entry point to create and verify full project structure.
    """
    create_directory_structure()
    if verify_full_structure():
        print("\nFull project structure created and verified successfully.")
        return 0
    else:
        print("\nProject structure verification failed.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())