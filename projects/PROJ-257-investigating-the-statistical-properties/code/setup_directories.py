import os
from pathlib import Path

def create_directories():
    """
    Orchestrate the creation of the entire project directory structure.
    This function calls the specific creation functions for data, src, and test directories.
    """
    from create_data_dirs import create_directories as create_data
    from create_src_dirs import create_directories as create_src
    from create_test_dirs import create_directories as create_tests
    
    # Execute creation in logical order
    print("Initializing project directory structure...")
    
    create_data()
    create_src()
    create_tests()
    
    print("All project directories initialized successfully.")

def main():
    create_directories()

if __name__ == "__main__":
    main()
