"""
State management utilities for tracking project progress and governance.
Provides functions to load, update, and manage project state files.
"""
import os
import yaml
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_state_file(state_file_path: Path) -> Dict[str, Any]:
    """
    Load a YAML state file and return its contents as a dictionary.
    
    Args:
        state_file_path: Path to the state YAML file
        
    Returns:
        Dictionary containing the state file contents
        
    Raises:
        FileNotFoundError: If the state file doesn't exist
        yaml.YAMLError: If the file contains invalid YAML
    """
    if not state_file_path.exists():
        raise FileNotFoundError(f"State file not found: {state_file_path}")
    
    with open(state_file_path, 'r', encoding='utf-8') as f:
        state = yaml.safe_load(f)
    
    return state if state else {}

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file's contents.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the file's SHA-256 hash
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot compute hash: file not found - {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def update_project_state(
    state_file_path: Path,
    project_id: str,
    completed_tasks: Optional[list] = None,
    current_task: Optional[str] = None,
    status: str = "in_progress",
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update a project's state file with new information.
    
    This function:
    1. Loads the existing state file
    2. Updates the artifact_hashes with hashes of relevant artifacts
    3. Updates the updated_at timestamp
    4. Updates task completion status
    5. Saves the updated state back to the file
    
    Args:
        state_file_path: Path to the project state YAML file
        project_id: The project identifier
        completed_tasks: List of task IDs that are now complete
        current_task: The current task being worked on
        status: Overall project status (e.g., "completed", "in_progress")
        notes: Optional notes about the update
        
    Returns:
        The updated state dictionary
        
    Raises:
        FileNotFoundError: If the state file doesn't exist
        yaml.YAMLError: If the file contains invalid YAML
    """
    # Load existing state
    state = load_state_file(state_file_path)
    
    # Ensure required sections exist
    if "project_id" not in state:
        state["project_id"] = project_id
    
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    if "tasks" not in state:
        state["tasks"] = {}
    
    if "governance" not in state:
        state["governance"] = {}
    
    # Update artifact hashes for key governance files
    governance_files = [
        Path("constitution.md"),
        Path("spec.md"),
        Path("plan.md")
    ]
    
    for file_path in governance_files:
        if file_path.exists():
            file_hash = compute_file_hash(file_path)
            state["artifact_hashes"][file_path.name] = file_hash
        else:
            logger.warning(f"Governance file not found: {file_path}")
    
    # Update task completion status
    if completed_tasks:
        for task_id in completed_tasks:
            state["tasks"][task_id] = {
                "status": "completed",
                "completed_at": datetime.now().isoformat()
            }
    
    # Update current task if provided
    if current_task:
        state["tasks"][current_task] = {
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        }
    
    # Update overall status
    state["status"] = status
    
    # Update timestamp
    state["updated_at"] = datetime.now().isoformat()
    
    # Add notes if provided
    if notes:
        if "notes" not in state:
            state["notes"] = []
        state["notes"].append({
            "timestamp": datetime.now().isoformat(),
            "content": notes
        })
    
    # Save updated state
    with open(state_file_path, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated state file: {state_file_path}")
    return state
