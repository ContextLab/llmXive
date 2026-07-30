import os
from pathlib import Path
import yaml
from datetime import datetime

def create_state_structure():
    """
    Create the initial state structure for the project.
    This includes creating the state file and any necessary subdirectories.
    """
    base_path = Path(__file__).resolve().parent.parent
    state_dir = base_path / "state" / "projects"
    
    if not state_dir.exists():
        state_dir.mkdir(parents=True, exist_ok=True)
    
    project_id = "PROJ-122-identifying-structure-property-relations"
    state_file = state_dir / f"{project_id}.yaml"
    
    if not state_file.exists():
        initial_state = {
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "status": "initialized",
            "artifacts": {},
            "checksums": {},
            "pipeline_runs": []
        }
        
        with open(state_file, 'w') as f:
            yaml.dump(initial_state, f, default_flow_style=False)
        
        return state_file
    
    return state_file

if __name__ == "__main__":
    result = create_state_structure()
    print(f"State structure created at: {result}")
