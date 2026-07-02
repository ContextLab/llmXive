"""
Configuration module for the llmXive plant disease resistance pipeline.

Handles loading environment variables and setting default paths for the project.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Project root is assumed to be the parent of the 'code' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default directory structure
DEFAULT_DIRS = {
    "code": "code",
    "data": "data",
    "data_raw": "data/raw",
    "data_processed": "data/processed",
    "artifacts": "artifacts",
    "artifacts_models": "artifacts/models",
    "artifacts_reports": "artifacts/reports",
    "artifacts_figures": "artifacts/figures",
    "tests": "tests",
    "specs": "specs",
}

# Environment variable keys
ENV_DATA_DIR = "LLMXIVE_DATA_DIR"
ENV_MODEL_DIR = "LLMXIVE_MODEL_DIR"
ENV_REPORT_DIR = "LLMXIVE_REPORT_DIR"
ENV_LOG_LEVEL = "LLMXIVE_LOG_LEVEL"
ENV_SEED = "LLMXIVE_SEED"

# Default values
DEFAULT_SEED = 42
DEFAULT_LOG_LEVEL = "INFO"


def get_path(base_dir: str, *subdirs: str) -> Path:
    """
    Construct a full path relative to the project root.

    Args:
        base_dir: One of the keys in DEFAULT_DIRS (e.g., 'data', 'artifacts')
        *subdirs: Additional subdirectories to append.

    Returns:
        A resolved Path object.
    """
    if base_dir not in DEFAULT_DIRS:
        raise ValueError(f"Unknown base directory key: {base_dir}")
    
    base_path = _PROJECT_ROOT / DEFAULT_DIRS[base_dir]
    return base_path.joinpath(*subdirs)


def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables and defaults.

    Returns:
        A dictionary containing the configuration settings.
    """
    # Resolve data directories (allow override via env vars)
    data_root = os.environ.get(ENV_DATA_DIR)
    if data_root:
        data_path = Path(data_root)
    else:
        data_path = get_path("data")

    model_path = get_path("artifacts_models") if not os.environ.get(ENV_MODEL_DIR) else Path(os.environ.get(ENV_MODEL_DIR))
    report_path = get_path("artifacts_reports") if not os.environ.get(ENV_REPORT_DIR) else Path(os.environ.get(ENV_REPORT_DIR))

    # Ensure directories exist
    for path in [data_path, model_path, report_path]:
        path.mkdir(parents=True, exist_ok=True)

    return {
        "project_root": _PROJECT_ROOT,
        "data": {
            "raw": data_path / "raw",
            "processed": data_path / "processed",
            "manifest": data_path / "data_manifest.yaml",
        },
        "artifacts": {
            "models": model_path,
            "reports": report_path,
            "figures": get_path("artifacts_figures"),
        },
        "logging": {
            "level": os.environ.get(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL),
            "log_file": get_path("artifacts_reports") / "pipeline.log",
        },
        "random_seed": int(os.environ.get(ENV_SEED, DEFAULT_SEED)),
    }


# Pre-load configuration for convenience
CONFIG = load_config()

# Expose convenient paths
DATA_RAW_DIR = CONFIG["data"]["raw"]
DATA_PROCESSED_DIR = CONFIG["data"]["processed"]
DATA_MANIFEST_PATH = CONFIG["data"]["manifest"]
ARTIFACTS_MODELS_DIR = CONFIG["artifacts"]["models"]
ARTIFACTS_REPORTS_DIR = CONFIG["artifacts"]["reports"]
ARTIFACTS_FIGURES_DIR = CONFIG["artifacts"]["figures"]
LOG_LEVEL = CONFIG["logging"]["level"]
LOG_FILE = CONFIG["logging"]["log_file"]
RANDOM_SEED = CONFIG["random_seed"]