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
        project_root: Path to the project root directory
        project_id: The project identifier (e.g., PROJ-374-...)
    
    Returns:
        Path to the created YAML file
    """
    projects_dir = project_root / "state" / "projects"
    state_file = projects_dir / f"{project_id}.yaml"
    
    initial_state = {
        "project_id": project_id,
        "status": "initialized",
        "created_at": None,
        "updated_at": None,
        "phase": "Phase 2: Foundational",
        "completed_tasks": [],
        "current_task": None,
        "metrics": {},
        "data_files": {
            "raw": [],
            "processed": []
        },
        "models": {},
        "figures": [],
        "reports": []
    }
    
    with open(state_file, 'w') as f:
        yaml.dump(initial_state, f, default_flow_style=False, sort_keys=False)
    
    return state_file

def update_project_state(project_root: Path, project_id: str, updates: Dict[str, Any]) -> None:
    """
    Update an existing project state file with new information.
    
    Args:
        project_root: Path to the project root directory
        project_id: The project identifier
        updates: Dictionary of key-value pairs to update
    """
    state_file = project_root / "state" / "projects" / f"{project_id}.yaml"
    
    if not state_file.exists():
        raise FileNotFoundError(f"State file not found: {state_file}")
    
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    for key, value in updates.items():
        state[key] = value
    
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def main():
    """
    Main entry point for setting up state directories and initial project state.
    """
    # Determine project root (assuming this script is in code/ directory)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    project_id = "PROJ-374-predicting-the-influence-of-alloying-on-"
    
    print(f"Setting up state directories for project: {project_id}")
    
    # Ensure directories exist
    ensure_state_directories(project_root)
    print(f"  Created state directories under: {project_root / 'state'}")
    
    # Create initial project state file
    state_file = create_initial_project_state(project_root, project_id)
    print(f"  Created initial state file: {state_file}")
    
    # Update with creation timestamp
    from datetime import datetime
    now = datetime.utcnow().isoformat() + "Z"
    update_project_state(
        project_root, 
        project_id, 
        {
            "created_at": now,
            "updated_at": now,
            "completed_tasks": ["T001a", "T001b", "T002a", "T002b", "T003", "T004", "T005", "T006", "T007", "T008", "T009"]
        }
    )
    print(f"  Updated state with initialization metadata")
    
    print("State setup complete.")

if __name__ == "__main__":
    main()
