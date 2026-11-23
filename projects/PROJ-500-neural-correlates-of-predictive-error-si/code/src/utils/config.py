import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from .logging import get_logger

logger = get_logger(__name__)

class Config:
    """
    Centralized configuration management for the project.
    Loads from environment variables or defaults.
    """
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
        self._config_cache: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from environment or defaults."""
        self.data_dir = Path(os.getenv("DATA_DIR", "data"))
        self.seed = int(os.getenv("SEED", "42"))
        self.ram_limit_gb = float(os.getenv("RAM_LIMIT", "7.0"))
        
        # EEG Processing Parameters
        self.low_freq_filter_hz = float(os.getenv("LOW_FREQ_FILTER_HZ", "1.0"))
        self.high_freq_filter_hz = float(os.getenv("HIGH_FREQ_FILTER_HZ", "40.0"))
        
        # Epoching
        epoch_window_str = os.getenv("EPOCH_WINDOW", "-200,500")
        try:
            parts = [int(x.strip()) for x in epoch_window_str.split(",")]
            self.epoch_window_start = parts[0]
            self.epoch_window_end = parts[1]
        except (ValueError, IndexError):
            self.epoch_window_start = -200
            self.epoch_window_end = 500
            logger.warning(f"Invalid EPOCH_WINDOW format '{epoch_window_str}', using defaults: {self.epoch_window_start} to {self.epoch_window_end}")

        # Behavioral Binning (Task T021 Requirement)
        acc_block_size_str = os.getenv("ACCURACY_BLOCK_SIZE", "50")
        try:
            self.accuracy_block_size = int(acc_block_size_str)
        except ValueError:
            self.accuracy_block_size = 50
            logger.warning(f"Invalid ACCURACY_BLOCK_SIZE '{acc_block_size_str}', using default: {self.accuracy_block_size}")

        # Lagged Alignment
        lag_window_str = os.getenv("LAG_WINDOW", "10,20")
        try:
            parts = [int(x.strip()) for x in lag_window_str.split(",")]
            self.lag_window_start = parts[0]
            self.lag_window_end = parts[1]
        except (ValueError, IndexError):
            self.lag_window_start = 10
            self.lag_window_end = 20
            logger.warning(f"Invalid LAG_WINDOW format '{lag_window_str}', using defaults: {self.lag_window_start} to {self.lag_window_end}")

        # Power Analysis Thresholds
        self.min_subjects = int(os.getenv("MIN_SUBJECTS", "20"))
        self.min_trials_per_condition = int(os.getenv("MIN_TRIALS_PER_CONDITION", "500"))

    def get_accuracy_block_size(self) -> int:
        """Returns the number of trials per behavioral block."""
        return self.accuracy_block_size

    def get_epoch_window(self) -> tuple:
        """Returns the epoch window (start, end) in ms."""
        return (self.epoch_window_start, self.epoch_window_end)

    def get_data_dir(self) -> Path:
        """Returns the data directory path."""
        return self.data_dir

    def get_lag_window(self) -> tuple:
        """Returns the lag window (start, end) in trials."""
        return (self.lag_window_start, self.lag_window_end)

# Singleton instance helper
def get_config() -> Config:
    return Config()

def get_accuracy_block_size() -> int:
    return get_config().get_accuracy_block_size()

def get_epoch_window() -> tuple:
    return get_config().get_epoch_window()

def get_data_dir() -> Path:
    return get_config().get_data_dir()

def get_lag_window() -> tuple:
    return get_config().get_lag_window()
