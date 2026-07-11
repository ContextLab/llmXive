"""
update_state.py

Implements Constitution Principle V: State Management.
Updates the project state YAML file located at `state/projects/{project_id}.yaml`.
This script is designed to be run by the pipeline to record task completion,
artifact generation, and execution status.
"""

import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
import argparse
import json

# Project root is assumed to be the parent of 'scripts'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
PROJECT_ID = "PROJ-953-llmxive-follow-up-extending-code-as-agen"
STATE_FILE = STATE_DIR / f"{PROJECT_ID}.yaml"

def ensure_state_file_exists():
    """Creates the state directory and initializes the state file if it doesn't exist."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    if not STATE_FILE.exists():
        initial_state = {
            "project_id": PROJECT_ID,
            "created_at": datetime.now().isoformat(),
            "last_updated": None,
            "tasks": {},
            "artifacts": {},
            "status": "in_progress"
        }
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(initial_state, f, default_flow_style=False, sort_keys=False)
        return initial_state
    
    with open(STATE_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def update_task_status(task_id: str, status: str, details: dict = None):
    """
    Updates the status of a specific task in the state file.
    
    Args:
        task_id: The ID of the task (e.g., 'T005').
        status: The new status (e.g., 'completed', 'failed', 'running').
        details: Optional dictionary of additional metadata to store.
    """
    state = ensure_state_file_exists()
    
    if "tasks" not in state:
        state["tasks"] = {}
    
    task_entry = {
        "task_id": task_id,
        "status": status,
        "updated_at": datetime.now().isoformat()
    }
    
    if details:
        task_entry.update(details)
    
    state["tasks"][task_id] = task_entry
    state["last_updated"] = datetime.now().isoformat()
    
    # Update overall status if all tasks are completed (simple heuristic)
    # In a real scenario, this might depend on a specific list of required tasks
    if status == "completed":
        # Check if we want to auto-transition project status
        pass 

    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    print(f"Updated state for task {task_id}: {status}")

def register_artifact(artifact_path: str, artifact_type: str = "file", metadata: dict = None):
    """
    Registers a generated artifact in the state file.
    
    Args:
        artifact_path: Relative path to the artifact from project root.
        artifact_type: Type of artifact (file, directory, model, etc.).
        metadata: Optional metadata (size, checksum, etc.).
    """
    state = ensure_state_file_exists()
    
    if "artifacts" not in state:
        state["artifacts"] = []
    
    entry = {
        "path": str(artifact_path),
        "type": artifact_type,
        "registered_at": datetime.now().isoformat()
    }
    
    if metadata:
        entry["metadata"] = metadata
    
    # Avoid duplicates
    existing = [a for a in state["artifacts"] if a["path"] == str(artifact_path)]
    if not existing:
        state["artifacts"].append(entry)
    
    state["last_updated"] = datetime.now().isoformat()

    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    print(f"Registered artifact: {artifact_path}")

def main():
    parser = argparse.ArgumentParser(description="Update project state for llmXive pipeline.")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Subcommand: update_task
    parser_task = subparsers.add_parser("update_task", help="Update a specific task status")
    parser_task.add_argument("--task-id", required=True, help="Task ID (e.g., T005)")
    parser_task.add_argument("--status", required=True, choices=["completed", "failed", "running"], help="Task status")
    parser_task.add_argument("--details", type=str, help="JSON string of additional details")

    # Subcommand: register_artifact
    parser_artifact = subparsers.add_parser("register_artifact", help="Register a generated artifact")
    parser_artifact.add_argument("--path", required=True, help="Path to the artifact")
    parser_artifact.add_argument("--type", default="file", help="Type of artifact")
    parser_artifact.add_argument("--metadata", type=str, help="JSON string of metadata")

    args = parser.parse_args()

    if args.command == "update_task":
        details = {}
        if args.details:
            try:
                details = json.loads(args.details)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON for details: {args.details}", file=sys.stderr)
                sys.exit(1)
        update_task_status(args.task_id, args.status, details)
    
    elif args.command == "register_artifact":
        metadata = {}
        if args.metadata:
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON for metadata: {args.metadata}", file=sys.stderr)
                sys.exit(1)
        register_artifact(args.path, args.type, metadata)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()