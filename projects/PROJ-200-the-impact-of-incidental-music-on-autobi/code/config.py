import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

def get_project_root() -> Path:
    """Returns the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def ensure_directories(paths: List[Path]) -> None:
    """Creates directories if they don't exist."""
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)

def get_config_dict() -> Dict[str, Any]:
    """Returns a dictionary containing project configuration parameters."""
    return {
        "project_root": str(get_project_root()),
        "data_dir": Path(get_project_root()) / "data",
        "raw_data_dir": Path(get_project_root()) / "data" / "raw",
        "processed_data_dir": Path(get_project_root()) / "data" / "processed",
        "final_data_dir": Path(get_project_root()) / "data" / "final",
        "levenshtein_threshold": 4,
        "seed": 42,
        "fallback_flag": False,
        "MATCH_RATE_THRESHOLD": 0.6
    }

if __name__ == "__main__":
    config = get_config_dict()
    print(f"Project Root: {config['project_root']}")
    print(f"Data Directory: {config['data_dir']}")