"""
Configuration management for the Neural Correlates of Predictive Error Signals project.
Handles paths, seeds, and analysis parameters.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Project Root (relative to this file's location structure)
# We assume this file is at code/src/utils/config.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_CODE_DIR = _PROJECT_ROOT / "code"

# Ensure directories exist
_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Environment Variable Defaults
_ENV_DATA_DIR = os.getenv("DATA_DIR", str(_DATA_DIR))
_ENV_SEED = int(os.getenv("SEED", "42"))
_ENV_RAM_LIMIT = float(os.getenv("RAM_LIMIT", "7.0"))

# Analysis Parameters
# Filter settings (Hz)
FILTER_LOW = 1.0
FILTER_HIGH = 40.0

# Epoching settings (ms)
EPOCH_WINDOW_START = -200
EPOCH_WINDOW_END = 500

# Behavioral Binning Settings
# FR-005: Configurable multi-trial block for accuracy calculation
ACCURACY_BLOCK_SIZE = 20  # Number of trials per block for accuracy calculation

# Lagged Alignment Settings
LAG_WINDOW_START = -10  # Trials relative to current block (negative = past)
LAG_WINDOW_END = -1     # Trials relative to current block (exclusive end)

# Power Analysis Thresholds (Static)
MIN_SUBJECTS = 20
MIN_TRIALS_PER_CONDITION = 500

# Learning Phase Binning
LEARNING_PHASE_EARLY_THRESHOLD = 0.33  # Fraction of total trials
LEARNING_PHASE_LATE_THRESHOLD = 0.66   # Fraction of total trials

class Config:
    """Singleton-like configuration holder."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.logger = logging.getLogger(__name__)
        self._config = {
            "project_root": str(_PROJECT_ROOT),
            "data_dir": _ENV_DATA_DIR,
            "seed": _ENV_SEED,
            "ram_limit_gb": _ENV_RAM_LIMIT,
            "filter_low_hz": FILTER_LOW,
            "filter_high_hz": FILTER_HIGH,
            "epoch_window_start_ms": EPOCH_WINDOW_START,
            "epoch_window_end_ms": EPOCH_WINDOW_END,
            "accuracy_block_size": ACCURACY_BLOCK_SIZE,
            "lag_window_start_trials": LAG_WINDOW_START,
            "lag_window_end_trials": LAG_WINDOW_END,
            "min_subjects": MIN_SUBJECTS,
            "min_trials_per_condition": MIN_TRIALS_PER_CONDITION,
            "learning_phase_early_frac": LEARNING_PHASE_EARLY_THRESHOLD,
            "learning_phase_late_frac": LEARNING_PHASE_LATE_THRESHOLD,
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        self._config[key] = value
        self.logger.info(f"Config updated: {key} = {value}")

    def get_data_dir(self) -> Path:
        return Path(self._config["data_dir"])

    def get_epoch_window(self) -> tuple:
        return (self._config["epoch_window_start_ms"], self._config["epoch_window_end_ms"])

    def get_accuracy_block_size(self) -> int:
        return self._config["accuracy_block_size"]

    def get_lag_window(self) -> tuple:
        return (self._config["lag_window_start_trials"], self._config["lag_window_end_trials"])

    def save_to_file(self, path: Optional[Path] = None):
        if path is None:
            path = self.get_data_dir() / "config_snapshot.json"
        with open(path, 'w') as f:
            # Convert Path objects to strings for JSON
            serializable = {k: str(v) if isinstance(v, Path) else v for k, v in self._config.items()}
            json.dump(serializable, f, indent=2)

    def load_from_file(self, path: Path):
        if not path.exists():
            self.logger.warning(f"Config file not found: {path}, using defaults.")
            return
        with open(path, 'r') as f:
            loaded = json.load(f)
            # Basic type coercion if needed, but mostly direct assignment
            for k, v in loaded.items():
                self._config[k] = v
        self.logger.info(f"Config loaded from {path}")

# Global instance
config = Config()

# Helper functions for direct access
def get_accuracy_block_size() -> int:
    return config.get_accuracy_block_size()

def get_epoch_window() -> tuple:
    return config.get_epoch_window()

def get_data_dir() -> Path:
    return config.get_data_dir()

def get_lag_window() -> tuple:
    return config.get_lag_window()
