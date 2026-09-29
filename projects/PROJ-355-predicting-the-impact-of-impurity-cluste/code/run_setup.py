import sys
from pathlib import Path
from setup_project import main as setup_main

def main():
    """
    Entry point for the project setup script.
    """
    # Add the code directory to the path so imports work correctly
    # This script is expected to be run from the project root or code directory
    # We ensure the code directory is in sys.path
    code_dir = Path(__file__).resolve().parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    # Import and run the main setup function
    return setup_main()

if __name__ == "__main__":
    sys.exit(main())
