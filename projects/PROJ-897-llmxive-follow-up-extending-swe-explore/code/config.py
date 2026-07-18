"""
Configuration module for llmXive project.
Defines paths, seeds, and model configurations.
"""
import os
from pathlib import Path
from typing import Final, Dict, Any
from datetime import datetime


# Project root
PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent

# Configuration defaults
DEFAULT_CONFIG: Final = {
    "RANDOM_SEED": 42,
    "CPU_ONLY": True,
    "MAX_WORKERS": 2,
    "HARD_INSTANCE_PERCENTILE": 0.2,
    "VALIDATION_SAMPLE_SIZE": 20,
    "TURN_LIMIT_DEFAULT": 3,
    "SWEEP_SAMPLE_SIZE": 20,
    "SWEEP_TURN_LIMIT": 4,
    "TIMEOUT_HOURS": 6.0,
    "timestamp": datetime.now().isoformat()
}


def get_path(*subdirs: str) -> Path:
    """
    Get a path relative to the project root.
    
    Args:
        *subdirs: Subdirectory components.
    
    Returns:
        Path object.
    """
    return PROJECT_ROOT / "data" / Path(*subdirs)


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    dirs = [
        "raw",
        "curated",
        "results",
        "agent_logs",
        "figures",
        "paper"
    ]
    
    for d in dirs:
        (PROJECT_ROOT / "data" / d).mkdir(parents=True, exist_ok=True)
    
    (PROJECT_ROOT / "code" / "utils").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "tests").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "contracts").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "docs").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "paper").mkdir(parents=True, exist_ok=True)


def get_config_summary() -> Dict[str, Any]:
    """
    Get a summary of the current configuration.
    
    Returns:
        Dictionary of configuration values.
    """
    return DEFAULT_CONFIG.copy()


if __name__ == "__main__":
    print("Project Root:", PROJECT_ROOT)
    print("Config Summary:", get_config_summary())