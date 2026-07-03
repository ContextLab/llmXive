import os
import json
from pathlib import Path
from typing import Dict, Any, List

# Default configuration values
DEFAULT_CONFIG = {
    "max_tokens": 4000,
    "github_token": os.getenv("GITHUB_TOKEN", ""),
    "target_repos": [
        "microsoft/vscode",
        "python/cpython",
        "pytorch/pytorch"
    ],
    "random_seed": 42,
    "paths": {
        "data_raw": "data/raw",
        "data_derived": "data/derived",
        "data_annotations": "data/annotations",
        "results": "results",
        "tests": "tests",
        "specs": "specs",
        "src": "src",
        "logs": "logs"
    }
}

_config = None

def get_config() -> Dict[str, Any]:
    global _config
    if _config is None:
        _config = DEFAULT_CONFIG.copy()
    return _config

def get_target_repos() -> List[str]:
    return get_config().get("target_repos", [])

def get_paths() -> Dict[str, str]:
    return get_config().get("paths", {})

def ensure_directories():
    """Create all required directories based on config paths."""
    paths = get_paths()
    for key, path_str in paths.items():
        if key != "src": # Skip src creation if it's source code
            path = Path(path_str)
            path.mkdir(parents=True, exist_ok=True)
            # print(f"Ensured directory: {path}")

if __name__ == "__main__":
    ensure_directories()
    print("Directories created successfully.")
