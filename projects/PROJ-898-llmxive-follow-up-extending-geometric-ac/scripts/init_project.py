import os
import sys

# Add the root of the project structure to the path to allow imports
# Assuming this script is run from the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

# Add the root to sys.path if not already present
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

def main():
    """
    Initialize the project structure for PROJ-898.
    
    This script orchestrates the creation of the required directory structure
    and .gitkeep files as per the implementation plan.
    """
    print("Initializing PROJ-898 project structure...")
    
    # Import the setup module from the code directory
    try:
        from setup_project_structure import create_directory_structure, create_gitkeep_files
    except ImportError:
        # Fallback if script is run from a different location
        sys.path.insert(0, os.path.join(root_dir, "code"))
        from setup_project_structure import create_directory_structure, create_gitkeep_files

    # Define the root of the project structure
    project_root = root_dir

    print(f"Target root: {project_root}")

    # Create the directory structure
    create_directory_structure(project_root)

    # Create .gitkeep files
    create_gitkeep_files(project_root)

    print("Project initialization complete.")

if __name__ == "__main__":
    main()
