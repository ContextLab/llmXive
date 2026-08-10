import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any

def ensure_state_directories(project_root: Path) -> None:
    """
    Ensure the state directory structure exists.
    Creates:
      - state/
      - state/projects/
    """
    state_dir = project_root / "state"
    projects_dir = state_dir / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    projects_dir.mkdir(parents=True, exist_ok=True)

def create_initial_project_state(project_root: Path, project_id: str) -> Path:
    """
    Create the initial project state YAML file.
    
    Args:
        project_root: Root directory of the project
        project_id: The project identifier (e.g., 'PROJ-374-...')
    
    Returns:
        Path to the created state file
    """
    projects_dir = project_root / "state" / "projects"
    ensure_state_directories(project_root)
    
    state_file = projects_dir / f"{project_id}.yaml"
    
    initial_state = {
        "project_id": project_id,
        "status": "initialized",
        "created_at": "2024-01-01T00:00:00Z",
        "last_updated": "2024-01-01T00:00:00Z",
        "phases": {
            "phase_1_setup": {
                "status": "pending",
                "tasks_completed": []
            },
            "phase_2_foundational": {
                "status": "pending",
                "tasks_completed": []
            },
            "phase_3_us1": {
                "status": "pending",
                "tasks_completed": []
            },
            "phase_4_us2": {
                "status": "pending",
                "tasks_completed": []
            },
            "phase_5_us3": {
                "status": "pending",
                "tasks_completed": []
            }
        },
        "metadata": {
            "description": "Predicting the Influence of Alloying on the Seebeck Coefficient Using Public Data",
            "version": "0.1.0"
        }
    }
    
    with open(state_file, 'w') as f:
        yaml.dump(initial_state, f, default_flow_style=False, sort_keys=False)
    
    return state_file

def update_project_state(project_root: Path, project_id: str, updates: Dict[str, Any]) -> Path:
    """
    Update an existing project state file with new information.
    
    Args:
        project_root: Root directory of the project
        project_id: The project identifier
        updates: Dictionary of updates to apply
    
    Returns:
        Path to the updated state file
    """
    state_file = project_root / "state" / "projects" / f"{project_id}.yaml"
    
    if not state_file.exists():
        raise FileNotFoundError(f"State file not found: {state_file}")
    
    with open(state_file, 'r') as f:
        current_state = yaml.safe_load(f)
    
    # Apply updates recursively
    def update_dict(base: Dict, updates: Dict) -> None:
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                update_dict(base[key], value)
            else:
                base[key] = value
    
    update_dict(current_state, updates)
    
    # Update timestamp
    from datetime import datetime
    current_state["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    with open(state_file, 'w') as f:
        yaml.dump(current_state, f, default_flow_style=False, sort_keys=False)
    
    return state_file

def main() -> None:
    """
    Main entry point for setting up state directories and initial project state.
    """
    project_root = Path(__file__).parent.parent
    project_id = "PROJ-374-predicting-the-influence-of-alloying-on-"
    
    print(f"Setting up state directories for project: {project_id}")
    ensure_state_directories(project_root)
    
    print(f"Creating initial project state file...")
    state_file = create_initial_project_state(project_root, project_id)
    
    print(f"State file created at: {state_file}")
    print(f"Directory structure ready:")
    print(f"  - {project_root / 'state'}")
    print(f"  - {project_root / 'state' / 'projects'}")

if __name__ == "__main__":
    main()
