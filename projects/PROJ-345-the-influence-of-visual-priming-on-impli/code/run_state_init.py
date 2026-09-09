import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from state_management import init_state_file

def main():
    """
    Initializes the state.yaml file for the current project (PROJ-345).
    This script fulfills the requirement for T007: Setup state structure and initialization.
    """
    project_id = "PROJ-345"
    print(f"Initializing state for project {project_id}...")
    state_path = init_state_file(project_id)
    print(f"State file created at: {state_path}")
    
    # Verify the file exists and has content
    if state_path.exists():
        with open(state_path, 'r') as f:
            content = f.read()
            if content:
                print("State initialization successful.")
                return 0
    print("State initialization failed or file is empty.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
