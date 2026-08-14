"""
Project configuration management.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

from utils.error_handlers import ConfigurationError

# Project root is parent of code/ directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

class Config:
    """Central configuration container."""
    
    def __init__(self):
        # Directories
        self.data_raw_dir = _PROJECT_ROOT / "data" / "raw"
        self.data_processed_dir = _PROJECT_ROOT / "data" / "processed"
        self.data_outputs_dir = _PROJECT_ROOT / "data" / "outputs"
        self.models_dir = _PROJECT_ROOT / "models"
        self.code_dir = _PROJECT_ROOT / "code"
        
        # Ingestion thresholds
        self.composition_sum_threshold = 0.95
        self.max_elements = 5
        
        # Validation thresholds
        self.vif_threshold = 5.0
        
        # Model training
        self.r2_sensitivity_thresholds = {"low": 0.4, "medium": 0.6, "high": 0.7}
        self.min_samples_warning = 50
        self.min_samples_target = 100
        self.cv_folds = 5
        self.bootstrap_iterations = 100
        
        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # Physical constants for conversion
        self.GPA_TO_HV = 10.197
        self.KGF_MM2_TO_HV = 9.807
        self.ROOM_TEMP_THRESHOLD_C = 25.0
        self.ROOM_TEMP_TOLERANCE_C = 5.0

    def validate(self):
        """Ensure critical paths exist."""
        critical_dirs = [
            self.data_raw_dir,
            self.data_processed_dir,
            self.data_outputs_dir,
            self.models_dir
        ]
        for d in critical_dirs:
            if not d.exists():
                # Don't raise here, allow setup scripts to create them
                pass

_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Retrieve the singleton config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

# Convenience getters
def get_data_raw_dir() -> Path:
    return get_config().data_raw_dir

def get_data_processed_dir() -> Path:
    return get_config().data_processed_dir

def get_data_outputs_dir() -> Path:
    return get_config().data_outputs_dir

def get_models_dir() -> Path:
    return get_config().models_dir

def get_composition_sum_threshold() -> float:
    return get_config().composition_sum_threshold

def get_max_elements() -> int:
    return get_config().max_elements

def get_vif_threshold() -> float:
    return get_config().vif_threshold

def get_r2_sensitivity_thresholds() -> Dict[str, float]:
    return get_config().r2_sensitivity_thresholds

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
