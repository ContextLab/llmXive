import os
import json
from pathlib import Path


def ensure_directory(dir_path: str) -> Path:
    """
    Creates a directory if it does not exist.
    Returns the Path object of the directory.
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def initialize_file(file_path: str, initial_content: dict = None) -> Path:
    """
    Creates a file if it does not exist.
    If initial_content is provided (dict), writes it as JSON.
    Returns the Path object of the file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not path.exists():
        if initial_content is not None:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(initial_content, f, indent=2)
        else:
            path.touch()
    
    return path


def main():
    """
    Main entry point to setup the project data structure and state tracking.
    Implements T004: Setup data/ directory structure and state tracking.
    """
    # Define project root relative to this script (assuming code/ is at root or similar)
    # We assume the script runs from the project root or code/ is a subdirectory.
    # Based on T001, the project root is projects/PROJ-444-...
    # We will use relative paths from the current working directory.
    
    base_dir = Path.cwd()
    
    # 1. Create data/ directory structure
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    logs_dir = data_dir / "logs"
    
    ensure_directory(str(data_dir))
    ensure_directory(str(raw_dir))
    ensure_directory(str(processed_dir))
    ensure_directory(str(logs_dir))
    
    print(f"Created data structure: {data_dir}, {raw_dir}, {processed_dir}, {logs_dir}")
    
    # 2. Create state/ directory for tracking
    state_dir = base_dir / "state"
    ensure_directory(str(state_dir))
    
    # 3. Initialize state tracking files
    # state/pipeline_state.json - tracks current step, version, and status
    state_file = state_dir / "pipeline_state.json"
    initial_state = {
        "pipeline_version": "1.0.0",
        "last_step": "T004_setup_data",
        "status": "initialized",
        "timestamp": None,
        "artifacts": {
            "data_raw": None,
            "data_processed": None,
            "models": None
        },
        "config": {
            "random_seed": 42,
            "target_metric": "R2"
        }
    }
    initialize_file(str(state_file), initial_state)
    
    # state/checkpoints.json - tracks completed tasks and their outputs
    checkpoints_file = state_dir / "checkpoints.json"
    initial_checkpoints = {
        "completed_tasks": [],
        "failed_tasks": [],
        "last_checkpoint": None
    }
    initialize_file(str(checkpoints_file), initial_checkpoints)
    
    # 4. Initialize .gitkeep files to ensure directories are tracked in git
    (data_dir / ".gitkeep").touch()
    (raw_dir / ".gitkeep").touch()
    (processed_dir / ".gitkeep").touch()
    (logs_dir / ".gitkeep").touch()
    (state_dir / ".gitkeep").touch()
    
    print(f"State tracking initialized at {state_dir}")
    print("T004 Setup complete.")


if __name__ == "__main__":
    main()