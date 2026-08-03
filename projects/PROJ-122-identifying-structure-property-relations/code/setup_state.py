import os
from pathlib import Path
import yaml
from datetime import datetime

def create_state_structure(project_root: Path) -> None:
    """
    Create the state directory structure and initialize the project state file.
    
    Args:
        project_root: The root directory of the project.
    """
    # Define the paths
    state_dir = project_root / "state"
    projects_dir = state_dir / "projects"
    
    # Create directories
    state_dir.mkdir(parents=True, exist_ok=True)
    projects_dir.mkdir(parents=True, exist_ok=True)
    
    # Define the project state file path
    project_id = "PROJ-122-identifying-structure-property-relations"
    state_file = projects_dir / f"{project_id}.yaml"
    
    # If the file already exists, do not overwrite it (preserve state)
    if state_file.exists():
        print(f"State file {state_file} already exists. Skipping creation.")
        return
    
    # Initialize the project state structure
    state_data = {
        "project_id": project_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": "initialized",
        "artifacts": {
            "raw_data": [],
            "processed_data": [],
            "features": [],
            "models": [],
            "reports": []
        },
        "checksums": {},
        "execution_log": []
    }
    
    # Write the YAML file
    with open(state_file, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"Created state file: {state_file}")

def main():
    """Main entry point for the script."""
    # Determine project root (assuming script is in code/ directory)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    create_state_structure(project_root)

if __name__ == "__main__":
    main()
