import os
from pathlib import Path
from typing import Literal, Dict, Any

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODE: Literal["CI", "RESEARCH"] = "CI"  # Default to CI for safety

def set_mode(mode: Literal["CI", "RESEARCH"]) -> None:
    """Set the execution mode."""
    global MODE
    if mode not in ["CI", "RESEARCH"]:
        raise ValueError(f"Invalid mode: {mode}. Must be 'CI' or 'RESEARCH'.")
    MODE = mode

def get_mode() -> Literal["CI", "RESEARCH"]:
    """Get current execution mode."""
    return MODE

def is_ci_mode() -> bool:
    return MODE == "CI"

def is_research_mode() -> bool:
    return MODE == "RESEARCH"

def get_config_summary() -> Dict[str, Any]:
    return {
        "mode": MODE,
        "project_root": str(PROJECT_ROOT),
    }

def get_path(relative_path: str) -> Path:
    """Resolve a path relative to the project root."""
    return PROJECT_ROOT / relative_path

def ensure_paths_exist() -> None:
    """Ensure all required directories exist."""
    dirs = [
        "data/raw",
        "data/processed/masked_images",
        "data/annotations",
        "data/results",
        "code/models",
        "tests/unit",
        "tests/integration",
    ]
    for d in dirs:
        get_path(d).mkdir(parents=True, exist_ok=True)
