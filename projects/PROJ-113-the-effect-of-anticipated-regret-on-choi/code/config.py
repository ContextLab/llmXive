import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project root relative to this file (assuming code/ is at root or one level down)
# We assume the project root is the parent of the 'code' directory.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Dataset URLs (from plan.md / spec amendments)
DATASET_URLS = {
    "zhehuderek/textual_decisionmaking_data": "zhehuderek/textual_decisionmaking_data",
    "PhillyMac/Decision_Making_Content_1": "PhillyMac/Decision_Making_Content_1"
}

def get_project_root() -> Path:
    return _PROJECT_ROOT

def get_path(relative_path: str) -> Path:
    return _PROJECT_ROOT / relative_path

def ensure_paths_exist() -> None:
    """Create necessary directories."""
    paths = [
        "data/raw",
        "data/processed",
        "data/results",
        "code/tests/unit",
        "code/tests/contract",
        "code/utils",
        "figures"
    ]
    for p in paths:
        get_path(p).mkdir(parents=True, exist_ok=True)

def get_dataset_url(dataset_name: str) -> str:
    return DATASET_URLS.get(dataset_name, dataset_name)

def get_config() -> Dict[str, Any]:
    return {
        "project_root": str(get_project_root()),
        "datasets": DATASET_URLS
    }

def get_model_config() -> Dict[str, Any]:
    return {
        "random_state": 42,
        "cv_folds": 5,
        "vif_threshold": 5.0
    }
