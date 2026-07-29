import os
from pathlib import Path
from typing import Literal, Dict, Any

# Mode definitions
MODE_CI: Literal["ci"] = "ci"
MODE_RESEARCH: Literal["research"] = "research"
ModeType = Literal["ci", "research"]

# Global mode state
_mode: ModeType = MODE_CI

# Project root (relative to this file)
PROJECT_ROOT: Path = Path(__file__).parent.parent

# Seed configuration
DEFAULT_SEED: int = 42

# Hyperparameters (shared defaults)
HYPERPARAMS: Dict[str, Any] = {
    "batch_size": 16,
    "learning_rate": 1e-4,
    "num_epochs": 10,
    "weight_decay": 1e-5,
    "mask_complexity_bins": 5,
    "min_mask_ratio": 0.1,
    "max_mask_ratio": 0.5,
}

# Path configuration (relative to PROJECT_ROOT)
PATHS: Dict[str, Path] = {
    "data_raw": PROJECT_ROOT / "data" / "raw",
    "data_processed": PROJECT_ROOT / "data" / "processed",
    "data_annotations": PROJECT_ROOT / "data" / "annotations",
    "data_results": PROJECT_ROOT / "data" / "results",
    "figures": PROJECT_ROOT / "figures",
    "models": PROJECT_ROOT / "code" / "models",
    "checkpoints": PROJECT_ROOT / "data" / "checkpoints",
    "logs": PROJECT_ROOT / "logs",
}

def get_mode() -> ModeType:
    """Return the current execution mode."""
    return _mode

def is_ci_mode() -> bool:
    """Check if running in CI mode."""
    return _mode == MODE_CI

def is_research_mode() -> bool:
    """Check if running in Research mode."""
    return _mode == MODE_RESEARCH

def set_mode(mode: ModeType) -> None:
    """Set the execution mode."""
    global _mode
    if mode not in (MODE_CI, MODE_RESEARCH):
        raise ValueError(f"Invalid mode: {mode}. Must be 'ci' or 'research'.")
    _mode = mode

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the current configuration."""
    return {
        "mode": _mode,
        "is_ci": is_ci_mode(),
        "is_research": is_research_mode(),
        "project_root": str(PROJECT_ROOT),
        "seed": DEFAULT_SEED,
        "paths": {k: str(v) for k, v in PATHS.items()},
        "hyperparams": HYPERPARAMS,
    }

def get_path(key: str) -> Path:
    """Retrieve a configured path by key.
    
    Args:
        key: One of the keys in PATHS (e.g., 'data_raw', 'models').
        
    Returns:
        The corresponding Path object.
        
    Raises:
        KeyError: If the key is not found in PATHS.
    """
    if key not in PATHS:
        raise KeyError(f"Path key '{key}' not found in configuration.")
    return PATHS[key]

def ensure_paths_exist() -> None:
    """Create all configured directories if they do not exist."""
    for p in PATHS.values():
        p.mkdir(parents=True, exist_ok=True)

# Initialize directories on import if in CI mode (optional behavior)
# Uncomment the line below if automatic directory creation is desired on import.
# ensure_paths_exist()