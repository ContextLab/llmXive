import os
import yaml
from datetime import datetime

PROJECT_ID = "PROJ-866-llmxive-follow-up-extending-foundation-p"

def create_state_directory(root_dir: str = ".") -> str:
    """
    Creates the state directory structure if it doesn't exist.
    Returns the path to the state directory.
    """
    state_dir = os.path.join(root_dir, "state", "projects")
    os.makedirs(state_dir, exist_ok=True)
    return state_dir

def create_initial_project_state(state_dir: str, project_id: str) -> str:
    """
    Creates an initial project state YAML file.
    Returns the path to the created file.
    """
    filepath = os.path.join(state_dir, f"{project_id}.yaml")
    
    state_data = {
        "project_id": project_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "status": "initialized",
        "phase": "Foundational",
        "completed_tasks": [],
        "artifacts": {
            "data_raw": [],
            "data_processed": [],
            "data_results": [],
            "figures": []
        },
        "metadata": {
            "description": "llmXive follow-up: extending Foundation Protocol",
            "spec_reference": "/specs/001-policy-compression-tradeoff/",
            "version": "0.1.0"
        }
    }
    
    with open(filepath, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    return filepath

def main():
    """
    Main entry point to initialize the state directory and project state file.
    """
    root_dir = "."
    state_dir = create_state_directory(root_dir)
    project_path = create_initial_project_state(state_dir, PROJECT_ID)
    print(f"Initialized project state at: {project_path}")

if __name__ == "__main__":
    main()
