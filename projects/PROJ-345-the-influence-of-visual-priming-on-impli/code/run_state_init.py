"""
Entry point script to initialize the state directory structure and state.yaml
for the current project (PROJ-345).
"""
import sys
from pathlib import Path

# Add parent directory to path to allow imports
parent_dir = Path(__file__).parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from state_management import init_state_file, get_path


def main():
    """
    Main function to initialize state for PROJ-345.
    """
    project_id = "PROJ-345"
    
    print(f"Initializing state for project: {project_id}")
    
    # Ensure the state directory structure exists
    state_dir = get_path("state")
    state_dir.mkdir(parents=True, exist_ok=True)
    
    projects_dir = state_dir / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    
    project_dir = projects_dir / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize the state.yaml file
    state_file = init_state_file(project_id)
    
    print(f"State initialization complete.")
    print(f"State file location: {state_file}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
