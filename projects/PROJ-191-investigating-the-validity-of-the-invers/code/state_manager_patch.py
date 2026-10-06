"""
Patch to ensure state_manager.py correctly handles the state file path and structure
if it wasn't fully implemented in previous tasks.
"""
import json
import os
from pathlib import Path
import logging
import yaml
from config import ProjectConfig, get_logger

def get_state_path() -> Path:
    """Returns the path to the project state YAML file."""
    config = ProjectConfig()
    # Assuming state is at project_root/state/projects/<project_id>.yaml
    return config.project_root / "state" / "projects" / "PROJ-191-investigating-the-inverse-square-law.yaml"

def read_state(path: Path = None) -> dict:
    """Reads the state YAML file."""
    if path is None:
        path = get_state_path()
    if not path.exists():
        return {"stages": {}, "pipeline_status": "not_started"}
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def write_state(path: Path, state: dict) -> None:
    """Writes the state dictionary to the YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def check_bootstrap_flag() -> bool:
    """Checks if bootstrap is needed (reads from config or run_count)."""
    run_count_path = Path("data/processed/run_count.json")
    if run_count_path.exists():
        with open(run_count_path, 'r') as f:
            data = json.load(f)
            return data.get("count", 0) < 3
    return False

def set_bootstrap_flag(flag: bool) -> None:
    """Sets the bootstrap flag in a config file if needed."""
    # Implementation depends on where this flag is stored, typically config.json
    config_path = Path("data/processed/config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        config["bootstrap_needed"] = flag
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)

def main():
    logger = get_logger()
    logger.info("State Manager Patch Loaded")
    # Example usage
    path = get_state_path()
    logger.info(f"State path: {path}")

if __name__ == "__main__":
    main()