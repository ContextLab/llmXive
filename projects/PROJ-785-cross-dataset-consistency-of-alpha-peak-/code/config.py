import os
from pathlib import Path
from typing import Final, List, Dict, Any, Optional
import json

# Project Root
_PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# Data Paths
_DATA_RAW: Final[Path] = _PROJECT_ROOT / "data" / "raw"
_DATA_DERIVATIVES: Final[Path] = _PROJECT_ROOT / "data" / "derivatives"
_DATA_PROCESSED: Final[Path] = _PROJECT_ROOT / "data" / "processed"
_STATE_DIR: Final[Path] = _PROJECT_ROOT / "state"

# OpenNeuro Dataset IDs (FR-001: at least 3 distinct)
# Verified sources: ds003865, ds003392, ds003775
OPENNEURO_DATASET_IDS: Final[List[str]] = [
    "ds003865",
    "ds003392",
    "ds003775"
]

# Processing Parameters
# Pipeline A (Standard)
PIPELINE_A_BANDPASS: Final[tuple] = (1.0, 45.0)  # Hz
PIPELINE_A_NOTCH_FREQ: Final[int] = 60  # Hz (default, overridden by metadata)
PIPELINE_A_REJECT_ICA_CORR: Final[float] = 0.8
PIPELINE_A_REJECT_ICA_VAR: Final[float] = 0.15

# Pipeline B (Alternative - Constitutional Override T000)
PIPELINE_B_BANDPASS: Final[tuple] = (0.5, 40.0)  # Hz
PIPELINE_B_NOTCH_FREQ: Final[int] = 60  # Hz (default, overridden by metadata)
# Pipeline B uses Mastoid Reference instead of CAR/ICA

# APF Estimation Parameters
ALPHA_BAND_LOW: Final[float] = 8.0
ALPHA_BAND_HIGH: Final[float] = 13.0
APF_CONSISTENCY_THRESHOLD: Final[float] = 0.5  # Hz
SENSITIVITY_SWEEP_STEP: Final[float] = 0.5  # Hz
POWER_THRESHOLD: Final[float] = 0.80
R_SQUARED_THRESHOLD: Final[float] = 0.30

# Random Seeds
GLOBAL_SEED: Final[int] = 42

def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    return _PROJECT_ROOT

def get_data_path() -> Path:
    """Return the absolute path to the data directory."""
    return _PROJECT_ROOT / "data"

def ensure_directories_exist() -> None:
    """Ensure all required data directories exist."""
    dirs = [_DATA_RAW, _DATA_DERIVATIVES, _DATA_PROCESSED, _STATE_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def validate_config() -> Dict[str, Any]:
    """
    Validate the current configuration.
    Returns a dictionary of validation status and any warnings/errors.
    """
    issues = []
    status = "ok"

    # Validate dataset IDs
    if not OPENNEURO_DATASET_IDS or len(OPENNEURO_DATASET_IDS) < 3:
        issues.append("FR-001 Violation: Must have at least 3 distinct dataset IDs.")
        status = "error"

    # Validate parameter ranges
    if PIPELINE_A_BANDPASS[0] >= PIPELINE_A_BANDPASS[1]:
        issues.append("Pipeline A bandpass low >= high.")
        status = "error"
    
    if PIPELINE_B_BANDPASS[0] >= PIPELINE_B_BANDPASS[1]:
        issues.append("Pipeline B bandpass low >= high.")
        status = "error"

    if ALPHA_BAND_LOW >= ALPHA_BAND_HIGH:
        issues.append("Alpha band low >= high.")
        status = "error"

    return {
        "status": status,
        "issues": issues,
        "datasets": OPENNEURO_DATASET_IDS,
        "pipelines": {
            "A": {
                "bandpass": PIPELINE_A_BANDPASS,
                "notch": PIPELINE_A_NOTCH_FREQ,
                "ica_corr": PIPELINE_A_REJECT_ICA_CORR,
                "ica_var": PIPELINE_A_REJECT_ICA_VAR
            },
            "B": {
                "bandpass": PIPELINE_B_BANDPASS,
                "notch": PIPELINE_B_NOTCH_FREQ
            }
        }
    }

# Helper to load optional overrides from a JSON file if it exists
def load_config_overrides(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load optional configuration overrides from a JSON file.
    If path is None, looks for 'config_override.json' in the project root.
    """
    if path is None:
        path = _PROJECT_ROOT / "config_override.json"
    
    if not path.exists():
        return {}
    
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # Log warning but return empty dict to avoid crashing
        print(f"Warning: Could not load config overrides from {path}: {e}")
        return {}
