import os
from pathlib import Path
from typing import Final, Dict, Any
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

PATHS: Dict[str, Path] = {
    "data_raw": BASE_DIR / "data" / "raw",
    "data_curated": BASE_DIR / "data" / "curated",
    "data_results": BASE_DIR / "data" / "results",
    "tests_unit": BASE_DIR / "tests" / "unit",
    "tests_contract": BASE_DIR / "tests" / "contract",
    "contracts": BASE_DIR / "contracts",
    "docs": BASE_DIR / "docs",
    "paper": BASE_DIR / "paper",
    "code": BASE_DIR / "code",
}

CONFIG: Dict[str, Any] = {
    "random_seed": 42,
    "cpu_only": True,
    "complexity_threshold": 50,
    "hard_instance_percentile": 0.20,
    "min_synthetic_issues": 10,
    "validation_sample_size": 5,
    "max_turns": 3,
    "force_quantization": True,
}

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    for path in PATHS.values():
        path.mkdir(parents=True, exist_ok=True)

def get_path(key: str) -> Path:
    """Get a specific path by key."""
    if key not in PATHS:
        raise KeyError(f"Path key '{key}' not found in PATHS")
    return PATHS[key]

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the current configuration."""
    return {
        "base_dir": str(BASE_DIR),
        "timestamp": datetime.now().isoformat(),
        "config": CONFIG,
        "paths": {k: str(v) for k, v in PATHS.items()}
    }