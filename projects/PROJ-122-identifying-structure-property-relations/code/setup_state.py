import os
from pathlib import Path
import yaml
from datetime import datetime

def create_state_structure(project_root: Path) -> None:
    """
    Create the directory structure for project state management.
    
    Creates:
    - state/projects/ directory
    
    Args:
        project_root: The root directory of the project
    """
    state_dir = project_root / "state"
    projects_dir = state_dir / "projects"
    
    # Create directories if they don't exist
    state_dir.mkdir(parents=True, exist_ok=True)
    projects_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Created state directory structure at: {state_dir}")
    print(f"Created projects directory at: {projects_dir}")

def main() -> None:
    """Main entry point for state structure creation."""
    # Determine project root (assuming script is in code/)
    project_root = Path(__file__).resolve().parent.parent
    
    create_state_structure(project_root)
    
    # Create the placeholder project state file
    project_id = "PROJ-122-identifying-structure-property-relations"
    state_file = project_root / "state" / "projects" / f"{project_id}.yaml"
    
    if not state_file.exists():
        state_data = {
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "initialized",
            "artifacts": {},
            "checksums": {},
            "metadata": {
                "description": "Identifying structure-property relationships in polymer blends",
                "version": "0.1.0"
            }
        }
        
        with open(state_file, "w", encoding="utf-8") as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        
        print(f"Created placeholder state file: {state_file}")
    else:
        print(f"State file already exists: {state_file}")

if __name__ == "__main__":
    main()
