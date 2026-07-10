"""
Base Data Loader and Validation Utilities.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import mne
from code.config import get_config

class DataLoaderError(Exception):
    """Base exception for data loading errors."""
    pass

class BaseDataLoader:
    """Abstract base class for data loaders."""
    def __init__(self, data_path: Path):
        self.data_path = data_path
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data path not found: {self.data_path}")

    def load(self) -> mne.io.Raw:
        raise NotImplementedError

def validate_sampling_rate(sfreq: float, threshold: float = 500.0) -> bool:
    """
    Validate that the sampling rate meets the minimum threshold.
    
    Args:
        sfreq: Sampling frequency in Hz.
        threshold: Minimum required sampling rate (default 500 Hz).
        
    Returns:
        True if valid, False otherwise.
    """
    return sfreq >= threshold

def validate_trial_counts(n_oddball: int, n_standard: int, min_oddball: int = 100, min_standard: int = 300) -> bool:
    """
    Validate that trial counts meet minimum requirements.
    
    Args:
        n_oddball: Number of oddball trials.
        n_standard: Number of standard trials.
        min_oddball: Minimum required oddball trials (default 100).
        min_standard: Minimum required standard trials (default 300).
        
    Returns:
        True if valid, False otherwise.
    """
    return (n_oddball >= min_oddball) and (n_standard >= min_standard)
