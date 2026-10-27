import seed
import sys
from setup_directories import create_directory_structure

def main():
    """
    Main entry point to execute the directory creation logic.
    Returns 0 on success, 1 on failure.
    """
    try:
        create_directory_structure()
        print("Project directory layout created successfully.")
        return 0
    except Exception as e:
        print(f"Error creating project directory layout: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())