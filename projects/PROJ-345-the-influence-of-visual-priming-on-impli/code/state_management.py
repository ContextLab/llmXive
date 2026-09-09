import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Import config to ensure we use the project's root and seed settings
try:
    from config import get_path
except ImportError:
    # Fallback for standalone execution if config isn't available yet
    from pathlib import Path
    def get_path(subpath: str) -> Path:
        base = Path(__file__).resolve().parent.parent
        return base / subpath

def get_state_root() -> Path:
    """Returns the root directory for state files."""
    return get_path("state")

def get_project_state_dir(project_id: str) -> Path:
    """Returns the specific state directory for a project."""
    state_root = get_state_root()
    return state_root / "projects" / project_id

def init_state_file(project_id: str, metadata: Optional[Dict[str, Any]] = None) -> Path:
    """
    Initializes the state.yaml file for a specific project.
    
    Creates the directory structure if it doesn't exist.
    Writes a default state structure including versioning info (Principle V).
    
    Args:
        project_id: The unique identifier for the project (e.g., 'PROJ-345')
        metadata: Optional initial metadata to merge into the state.
    
    Returns:
        Path to the created/updated state.yaml file.
    """
    project_dir = get_project_state_dir(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = project_dir / "state.yaml"
    
    # Define the default state structure for Principle V (Versioning)
    # This structure tracks artifacts, execution logs, and configuration snapshots
    default_state = {
        "project_id": project_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "principles": {
            "V": {
                "name": "Versioning",
                "status": "active",
                "artifacts": [],
                "execution_logs": []
            }
        },
        "artifacts": [],
        "execution_history": []
    }
    
    if metadata:
        default_state.update(metadata)
    
    # Ensure updated_at is current
    default_state["updated_at"] = datetime.utcnow().isoformat()
    
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(default_state, f, default_flow_style=False, sort_keys=False)
    
    logging.info(f"Initialized state file for project {project_id} at {state_file}")
    return state_file

def save_state_file(project_id: str, state_data: Dict[str, Any]) -> Path:
    """
    Saves the provided state dictionary to the project's state.yaml file.
    
    Args:
        project_id: The project identifier.
        state_data: The complete state dictionary to save.
    
    Returns:
        Path to the saved file.
    """
    project_dir = get_project_state_dir(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)
    state_file = project_dir / "state.yaml"
    
    state_data["updated_at"] = datetime.utcnow().isoformat()
    
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    return state_file

def add_artifact_record(project_id: str, artifact_path: str, checksum: Optional[str] = None, description: Optional[str] = None) -> None:
    """
    Adds a record of a generated artifact to the state.yaml file.
    
    Args:
        project_id: The project identifier.
        artifact_path: Relative path to the artifact.
        checksum: Optional checksum (e.g., SHA256) of the artifact.
        description: Optional description of the artifact.
    """
    state_file = get_project_state_dir(project_id) / "state.yaml"
    if not state_file.exists():
        raise FileNotFoundError(f"State file not found for project {project_id}. Run init_state_file first.")
    
    with open(state_file, "r", encoding="utf-8") as f:
        state_data = yaml.safe_load(f)
    
    record = {
        "path": str(artifact_path),
        "created_at": datetime.utcnow().isoformat(),
        "type": "artifact"
    }
    if checksum:
        record["checksum"] = checksum
    if description:
        record["description"] = description
    
    if "artifacts" not in state_data:
        state_data["artifacts"] = []
    
    state_data["artifacts"].append(record)
    save_state_file(project_id, state_data)

def log_execution(project_id: str, task_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs an execution event to the state.yaml file.
    
    Args:
        project_id: The project identifier.
        task_id: The ID of the task being executed.
        status: Execution status (e.g., 'completed', 'failed').
        details: Optional dictionary of execution details.
    """
    state_file = get_project_state_dir(project_id) / "state.yaml"
    if not state_file.exists():
        raise FileNotFoundError(f"State file not found for project {project_id}. Run init_state_file first.")
    
    with open(state_file, "r", encoding="utf-8") as f:
        state_data = yaml.safe_load(f)
    
    log_entry = {
        "task_id": task_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {}
    }
    
    if "execution_history" not in state_data:
        state_data["execution_history"] = []
    
    state_data["execution_history"].append(log_entry)
    save_state_file(project_id, state_data)

def main():
    """
    CLI entry point to initialize the state structure for a project.
    Usage: python code/state_management.py <project_id>
    """
    import sys
    if len(sys.argv) < 2:
        print("Usage: python code/state_management.py <project_id>")
        sys.exit(1)
    
    project_id = sys.argv[1]
    init_state_file(project_id)
    print(f"State initialized for {project_id}")

if __name__ == "__main__":
    main()
