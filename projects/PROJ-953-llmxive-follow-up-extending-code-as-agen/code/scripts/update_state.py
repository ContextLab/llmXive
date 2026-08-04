import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

def ensure_state_dirs(base_path: str = "state") -> Path:
    """Ensure state directories exist."""
    state_path = Path(base_path)
    state_path.mkdir(parents=True, exist_ok=True)
    (state_path / "projects").mkdir(exist_ok=True)
    return state_path

def load_state(project_id: str, base_path: str = "state") -> Dict[str, Any]:
    """Load state for a specific project."""
    state_file = Path(base_path) / "projects" / f"{project_id}.yaml"
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_state(project_id: str, state: Dict[str, Any], base_path: str = "state") -> None:
    """Save state for a specific project."""
    state_file = Path(base_path) / "projects" / f"{project_id}.yaml"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_task_status(project_id: str, task_id: str, status: str, base_path: str = "state") -> None:
    """Update the status of a specific task in the project state."""
    state = load_state(project_id, base_path)
    if "tasks" not in state:
        state["tasks"] = {}
    
    if task_id not in state["tasks"]:
        state["tasks"][task_id] = {}
    
    state["tasks"][task_id]["status"] = status
    state["tasks"][task_id]["updated_at"] = datetime.utcnow().isoformat()
    
    save_state(project_id, state, base_path)

def add_artifact(project_id: str, task_id: str, artifact_path: str, base_path: str = "state") -> None:
    """Add an artifact reference to a task in the project state."""
    state = load_state(project_id, base_path)
    if "tasks" not in state:
        state["tasks"] = {}
    
    if task_id not in state["tasks"]:
        state["tasks"][task_id] = {}
    
    if "artifacts" not in state["tasks"][task_id]:
        state["tasks"][task_id]["artifacts"] = []
    
    state["tasks"][task_id]["artifacts"].append({
        "path": artifact_path,
        "created_at": datetime.utcnow().isoformat()
    })
    
    save_state(project_id, state, base_path)

def main():
    """CLI entry point for state management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage project state")
    parser.add_argument("project_id", help="Project ID")
    parser.add_argument("--task", help="Task ID to update")
    parser.add_argument("--status", help="Status to set (completed, failed, etc.)")
    parser.add_argument("--artifact", help="Path to artifact to add")
    
    args = parser.parse_args()
    
    if args.status and args.task:
        update_task_status(args.project_id, args.task, args.status)
        print(f"Updated task {args.task} status to {args.status} for project {args.project_id}")
    
    if args.artifact and args.task:
        add_artifact(args.project_id, args.task, args.artifact)
        print(f"Added artifact {args.artifact} to task {args.task} for project {args.project_id}")

if __name__ == "__main__":
    main()
