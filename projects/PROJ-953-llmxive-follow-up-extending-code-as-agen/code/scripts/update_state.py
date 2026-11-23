"""
State Management Module.

Updates the project state YAML files to track task progress and artifacts.
Implements Constitution Principle V.
"""
import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

from config.loader import get_config

def ensure_state_dirs(state_dir: Path) -> None:
    """Ensure state directories exist."""
    state_dir.mkdir(parents=True, exist_ok=True)

def load_state(state_file: Path) -> Dict[str, Any]:
    """Load state from YAML file."""
    if not state_file.exists():
        return {"tasks": {}, "artifacts": []}
    with open(state_file, 'r') as f:
        return yaml.safe_load(f) or {"tasks": {}, "artifacts": []}

def save_state(state: Dict[str, Any], state_file: Path) -> None:
    """Save state to YAML file."""
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_task_status(task_id: str, status: str, state_file: Path) -> None:
    """Update the status of a specific task."""
    state = load_state(state_file)
    state["tasks"][task_id] = {
        "status": status,
        "updated_at": datetime.now().isoformat()
    }
    save_state(state, state_file)

def add_artifact(task_id: str, artifact_path: str, state_file: Path) -> None:
    """Add an artifact to the state associated with a task."""
    state = load_state(state_file)
    if "artifacts" not in state:
        state["artifacts"] = []
    state["artifacts"].append({
        "task_id": task_id,
        "path": artifact_path,
        "created_at": datetime.now().isoformat()
    })
    save_state(state, state_file)

def main():
    """Main entry point for state updates."""
    config = get_config()
    state_dir = Path(config.get("state_dir", "state"))
    ensure_state_dirs(state_dir)
    
    state_file = state_dir / "project_state.yaml"
    
    # Example usage: Update a task status
    # update_task_status("T037", "completed", state_file)
    # add_artifact("T037", "docs/README.md", state_file)
    
    print(f"State management ready. State file: {state_file}")

if __name__ == "__main__":
    main()
