"""
State management script for llmXive pipeline.
Updates project state files to track task progress and artifacts.
"""
import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

STATE_DIR = Path("state/projects")
PROJECT_NAME = "PROJ-953-llmxive-follow-up-extending-code-as-agen"

def ensure_state_dirs():
    """Ensure state directories exist."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def load_state():
    """Load current project state."""
    ensure_state_dirs()
    state_file = STATE_DIR / f"{PROJECT_NAME}.yaml"
    if state_file.exists():
        with open(state_file, 'r') as f:
            return yaml.safe_load(f) or {}
    return {"tasks": {}, "artifacts": [], "created_at": datetime.now().isoformat()}

def save_state(state):
    """Save project state to file."""
    ensure_state_dirs()
    state_file = STATE_DIR / f"{PROJECT_NAME}.yaml"
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def update_task_status(task_id: str, status: str):
    """Update the status of a specific task."""
    state = load_state()
    if "tasks" not in state:
        state["tasks"] = {}
    state["tasks"][task_id] = {
        "status": status,
        "updated_at": datetime.now().isoformat()
    }
    save_state(state)

def add_artifact(path: str, description: str):
    """Record a new artifact produced by the pipeline."""
    state = load_state()
    if "artifacts" not in state:
        state["artifacts"] = []
    state["artifacts"].append({
        "path": path,
        "description": description,
        "created_at": datetime.now().isoformat()
    })
    save_state(state)

def main():
    """CLI entry point for state updates."""
    import argparse
    parser = argparse.ArgumentParser(description="Update pipeline state")
    parser.add_argument("--task", type=str, help="Task ID to update")
    parser.add_argument("--status", type=str, help="New status (e.g., completed, failed)")
    parser.add_argument("--artifact", type=str, help="Path to new artifact")
    parser.add_argument("--desc", type=str, help="Description of artifact")
    args = parser.parse_args()

    if args.task and args.status:
        update_task_status(args.task, args.status)
        print(f"Updated task {args.task} to status {args.status}")
    if args.artifact and args.desc:
        add_artifact(args.artifact, args.desc)
        print(f"Added artifact: {args.artifact}")

if __name__ == "__main__":
    main()