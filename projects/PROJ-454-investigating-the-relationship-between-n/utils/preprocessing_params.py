"""
Preprocessing parameters configuration.
Used by T013 (02_preprocess_eeg.py).
"""
from typing import Dict, List, Any
import os

def get_preprocessing_params() -> Dict[str, Any]:
    """
    Returns a dictionary of preprocessing parameters.
    """
    return {
        "bandpass": (1.0, 45.0),  # Hz
        "notch": [50.0, 60.0],    # Hz (remove both 50 and 60 Hz noise)
        "epoch_duration": 2.0,    # seconds
        "n_components": 0.99,     # ICA components retention
        "ica_method": "fastica",
        "random_state": 42
    }

def get_data_quality_thresholds() -> Dict[str, Any]:
    """
    Returns thresholds for data quality checks.
    """
    return {
        "min_duration": 60.0,     # seconds
        "max_bad_ratio": 0.20,    # 20% bad channels allowed
        "max_artifacts": 0.10     # Max 10% epochs rejected (placeholder for future)
    }
