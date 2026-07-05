import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_state import main as setup_state_main
from setup_state_projects import main as setup_state_projects_main

def main() -> None:
    """
    Main entry point to run all state setup tasks.
    This orchestrates the creation of base state directories and project-specific directories.
    """
    print("Running State Setup...")
    
    # Run base state setup (if not already done by T002a, this ensures completeness)
    # Note: T002a creates the root state/ directory. This script focuses on project substructure.
    
    # Run project specific setup for PROJ-345
    print("Setting up project directories for PROJ-345...")
    setup_state_projects_main()
    
    print("State setup completed.")

if __name__ == "__main__":
    main()