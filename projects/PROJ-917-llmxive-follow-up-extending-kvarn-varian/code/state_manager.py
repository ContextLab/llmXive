"""
State management module for llmXive project.
Handles initialization and verification of project state files.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent

def get_state_dir() -> Path:
    """Get the state directory path."""
    return get_project_root() / "state"

def get_project_state_file(project_id: str) -> Path:
    """Get the path to a specific project's state file."""
    return get_state_dir() / "projects" / f"{project_id}.yaml"

def ensure_state_directory(project_id: str) -> Path:
    """Ensure the state directory for a project exists."""
    state_dir = get_state_dir() / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured state directory exists: {state_dir}")
    return state_dir

def initialize_project_state(project_id: str, initial_data: Optional[Dict[str, Any]] = None) -> Path:
    """
    Initialize a project state file with given data.
    
    Args:
        project_id: The project identifier
        initial_data: Initial data to write to the state file (default: empty dict)
        
    Returns:
        Path to the created state file
    """
    if initial_data is None:
        initial_data = {"artifact_hashes": {}}
    
    state_dir = ensure_state_directory(project_id)
    state_file = get_project_state_file(project_id)
    
    with open(state_file, 'w') as f:
        yaml.dump(initial_data, f, default_flow_style=False)
    
    logger.info(f"Initialized project state file: {state_file}")
    return state_file

def load_project_state(project_id: str) -> Dict[str, Any]:
    """
    Load the state file for a project.
    
    Args:
        project_id: The project identifier
        
    Returns:
        The state data as a dictionary
        
    Raises:
        FileNotFoundError: If the state file does not exist
    """
    state_file = get_project_state_file(project_id)
    
    if not state_file.exists():
        raise FileNotFoundError(f"State file not found for project {project_id}: {state_file}")
    
    with open(state_file, 'r') as f:
        return yaml.safe_load(f)

def update_project_state(project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the state file for a project with new values.
    
    Args:
        project_id: The project identifier
        updates: Dictionary of updates to apply
        
    Returns:
        The updated state data
    """
    state_file = get_project_state_file(project_id)
    
    if not state_file.exists():
        raise FileNotFoundError(f"State file not found for project {project_id}: {state_file}")
    
    current_state = load_project_state(project_id)
    current_state.update(updates)
    
    with open(state_file, 'w') as f:
        yaml.dump(current_state, f, default_flow_style=False)
    
    logger.info(f"Updated project state file: {state_file}")
    return current_state

def verify_project_state_exists(project_id: str) -> bool:
    """
    Verify that a project state file exists.
    
    Args:
        project_id: The project identifier
        
    Returns:
        True if the state file exists, False otherwise
    """
    state_file = get_project_state_file(project_id)
    exists = state_file.exists()
    if exists:
        logger.info(f"State file exists: {state_file}")
    else:
        logger.warning(f"State file missing: {state_file}")
    return exists

def main():
    """Main entry point for state management CLI."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Project state management")
    parser.add_argument("project_id", help="Project identifier")
    parser.add_argument("--init", action="store_true", help="Initialize state file")
    parser.add_argument("--verify", action="store_true", help="Verify state file exists")
    parser.add_argument("--show", action="store_true", help="Show current state")
    parser.add_argument("--update", help="JSON string of updates to apply")
    
    args = parser.parse_args()
    
    if args.init:
        path = initialize_project_state(args.project_id)
        print(f"Initialized: {path}")
    elif args.verify:
        exists = verify_project_state_exists(args.project_id)
        print(f"Exists: {exists}")
        sys.exit(0 if exists else 1)
    elif args.show:
        try:
            state = load_project_state(args.project_id)
            print(yaml.dump(state, default_flow_style=False))
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.update:
        import json
        try:
            updates = json.loads(args.update)
            state = update_project_state(args.project_id, updates)
            print(f"Updated state:\n{yaml.dump(state, default_flow_style=False)}")
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
