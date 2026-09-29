import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

def get_project_root() -> Path:
    """
    Returns the root directory of the project.
    Assumes the project is structured as:
    projects/PROJ-355-predicting-the-impact-of-impurity-cluste/
        code/
        data/
        ...
    This function looks for the 'code' directory relative to the current file.
    """
    # If this file is in code/, the project root is the parent of code/
    current_file_path = Path(__file__).resolve()
    code_dir = current_file_path.parent
    project_root = code_dir.parent
    
    # Verify the expected structure
    expected_dirs = ["data", "results", "tests"]
    for d in expected_dirs:
        if not (project_root / d).exists():
            # If not found, try to infer from cwd if running from a different context
            # But for the setup task, we assume the structure is created by setup_project.py
            pass
    
    return project_root

def get_data_paths() -> Dict[str, Path]:
    """
    Returns a dictionary of key data paths.
    """
    root = get_project_root()
    return {
        "raw": root / "data" / "raw",
        "processed": root / "data" / "processed",
        "potentials": root / "data" / "potentials",
        "metadata": root / "data" / "metadata.yaml"
    }

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a summary of the current configuration.
    """
    return {
        "project_root": str(get_project_root()),
        "data_paths": {k: str(v) for k, v in get_data_paths().items()}
    }

def save_config_snapshot(output_path: Optional[Path] = None) -> Path:
    """
    Saves the current configuration snapshot to a JSON file.
    """
    if output_path is None:
        output_path = get_project_root() / "results" / "config_snapshot.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    config = get_config_summary()
    config["timestamp"] = "2023-10-27T10:00:00Z" # Placeholder for actual timestamp logic if needed
    
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    return output_path
