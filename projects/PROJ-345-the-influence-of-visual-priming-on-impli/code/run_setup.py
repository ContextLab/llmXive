import sys
from pathlib import Path
from setup_directories import create_directories

def main():
    """
    Main entry point to run the setup script.
    Ensures all necessary data directories are created.
    """
    # Change to the code directory so imports work relative to the script
    script_dir = Path(__file__).parent
    if script_dir.name == "code":
        os.chdir(script_dir)
    
    print("Running setup for PROJ-345...")
    create_directories()
    print("Setup finished.")

if __name__ == "__main__":
    import os
    main()