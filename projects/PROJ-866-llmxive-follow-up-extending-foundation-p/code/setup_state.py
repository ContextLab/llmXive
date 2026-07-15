"""
State directory initialization script.
Creates state management structure and initial project state files.
"""
import os
import sys
from pathlib import Path
import yaml
from datetime import datetime

def create_state_directory():
    """
    Creates the state directory structure.
    """
    root = Path(__file__).parent.parent
    state_root = root / "state"
    
    subdirs = [
        "projects"
    ]
    
    created = []
    for subdir in subdirs:
        dir_path = state_root / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path.relative_to(root)))
    
    print(f"Created {len(created)} state subdirectories:")
    for item in sorted(created):
        print(f"  - {item}")
    
    return created

def create_initial_project_state(project_id: str):
    """
    Creates an initial state file for a specific project.
    """
    root = Path(__file__).parent.parent
    state_file = root / "state" / "projects" / f"{project_id}.yaml"
    
    if state_file.exists():
        print(f"State file already exists: {state_file}")
        return str(state_file.relative_to(root))
    
    initial_state = {
        "project_id": project_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "status": "initialized",
        "artifacts": {},
        "checksums": {},
        "metadata": {
            "pipeline_version": "1.0.0",
            "implementation_phase": "setup"
        }
    }
    
    with open(state_file, 'w') as f:
        yaml.dump(initial_state, f, default_flow_style=False, sort_keys=False)
    
    print(f"Created initial state file: {state_file}")
    return str(state_file.relative_to(root))

def main():
    """Entry point for script execution."""
    print("Initializing state directory...")
    create_state_directory()
    
    # Create initial state for the current project
    project_id = "PROJ-866-llmxive-follow-up-extending-foundation-p"
    create_initial_project_state(project_id)
    
    print("State directory initialization complete.")

if __name__ == "__main__":
    main()