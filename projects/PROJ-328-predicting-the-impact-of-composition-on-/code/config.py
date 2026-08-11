import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from utils.error_handlers import ConfigurationError

# Default configuration values
DEFAULT_MAX_ELEMENTS = 5
DEFAULT_R2_THRESHOLDS = {0.3, 0.5, 0.6, 0.7}
DEFAULT_ROOM_TEMP_THRESHOLD_C = 25
DEFAULT_ROOM_TEMP_TOLERANCE_C = 5
DEFAULT_COMPOSITION_SUM_THRESHOLD = 0.95
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_MIN_SAMPLES_WARNING = 50
DEFAULT_MIN_SAMPLES_TARGET = 100
DEFAULT_CV_FOLDS = 5
DEFAULT_BOOTSTRAP_ITERATIONS = 100
DEFAULT_VIF_THRESHOLD = 5

class Config:
    """Configuration class for the project."""
    def __init__(self):
        self.max_elements = int(os.getenv("MAX_ELEMENTS", DEFAULT_MAX_ELEMENTS))
        self.r2_thresholds = self._parse_r2_thresholds()
        self.room_temp_threshold_c = float(os.getenv("ROOM_TEMP_THRESHOLD_C", DEFAULT_ROOM_TEMP_THRESHOLD_C))
        self.room_temp_tolerance_c = float(os.getenv("ROOM_TEMP_TOLERANCE_C", DEFAULT_ROOM_TEMP_TOLERANCE_C))
        self.composition_sum_threshold = float(os.getenv("COMPOSITION_SUM_THRESHOLD", DEFAULT_COMPOSITION_SUM_THRESHOLD))
        self.log_level = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)
        self.log_format = os.getenv("LOG_FORMAT", DEFAULT_LOG_FORMAT)
        self.min_samples_warning = int(os.getenv("MIN_SAMPLES_WARNING", DEFAULT_MIN_SAMPLES_WARNING))
        self.min_samples_target = int(os.getenv("MIN_SAMPLES_TARGET", DEFAULT_MIN_SAMPLES_TARGET))
        self.cv_folds = int(os.getenv("CV_FOLDS", DEFAULT_CV_FOLDS))
        self.bootstrap_iterations = int(os.getenv("BOOTSTRAP_ITERATIONS", DEFAULT_BOOTSTRAP_ITERATIONS))
        self.vif_threshold = float(os.getenv("VIF_THRESHOLD", DEFAULT_VIF_THRESHOLD))

    def _parse_r2_thresholds(self) -> List[float]:
        """Parse R2 thresholds from environment variable or use default."""
        env_val = os.getenv("R2_THRESHOLDS")
        if env_val:
            try:
                # Expecting comma-separated floats, e.g., "0.3,0.5,0.6,0.7"
                return [float(x.strip()) for x in env_val.split(",")]
            except ValueError:
                raise ConfigurationError(f"Invalid R2_THRESHOLDS format: {env_val}")
        return list(DEFAULT_R2_THRESHOLDS)

# Singleton instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

# Helper functions for directory paths (assuming project root is where this file is or parent)
def _get_project_root() -> Path:
    current_file = Path(__file__).resolve()
    # Assume structure: code/config.py -> project_root
    return current_file.parent.parent

def get_data_raw_dir() -> Path:
    return _get_project_root() / "data" / "raw"

def get_data_processed_dir() -> Path:
    return _get_project_root() / "data" / "processed"

def get_data_outputs_dir() -> Path:
    return _get_project_root() / "data" / "outputs"

def get_models_dir() -> Path:
    return _get_project_root() / "models"

def get_composition_sum_threshold() -> float:
    return get_config().composition_sum_threshold

def get_max_elements() -> int:
    return get_config().max_elements

def get_vif_threshold() -> float:
    return get_config().vif_threshold

def get_r2_sensitivity_thresholds() -> List[float]:
    return get_config().r2_thresholds

def get_min_samples_warning() -> int:
    return get_config().min_samples_warning

def get_min_samples_target() -> int:
    return get_config().min_samples_target

def get_cv_folds() -> int:
    return get_config().cv_folds

def get_bootstrap_iterations() -> int:
    return get_config().bootstrap_iterations

def get_log_level() -> str:
    return get_config().log_level

def get_log_format() -> str:
    return get_config().log_format
