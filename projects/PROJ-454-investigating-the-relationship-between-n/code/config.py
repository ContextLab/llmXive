import os
from pathlib import Path
from typing import Dict, Any, Optional, List

class Config:
    """Configuration class for the project."""
    
    def __init__(
        self,
        openneuro_dataset_ids: List[str],
        min_age: int,
        output_dir: str,
        eeg_bandpass: tuple = (1, 45),
        notch_freqs: List[float] = None,
        snr_threshold_db: float = 5.0,
        max_ram_gb: float = 7.0,
        max_disk_gb: float = 14.0
    ):
        self.openneuro_dataset_ids = openneuro_dataset_ids
        self.min_age = min_age
        self.output_dir = output_dir
        self.eeg_bandpass = eeg_bandpass
        self.notch_freqs = notch_freqs or [50.0, 60.0]
        self.snr_threshold_db = snr_threshold_db
        self.max_ram_gb = max_ram_gb
        self.max_disk_gb = max_disk_gb

def load_config_from_env() -> Config:
    """Load configuration from environment variables."""
    # Default values
    dataset_ids_str = os.getenv("OPENNEURO_DATASET_IDS", "ds003104")
    dataset_ids = [d.strip() for d in dataset_ids_str.split(",") if d.strip()]
    
    min_age = int(os.getenv("MIN_AGE", "50"))
    output_dir = os.getenv("OUTPUT_DIR", "data/raw")
    snr_threshold = float(os.getenv("SNR_THRESHOLD_DB", "5.0"))
    
    return Config(
        openneuro_dataset_ids=dataset_ids,
        min_age=min_age,
        output_dir=output_dir,
        snr_threshold_db=snr_threshold
    )

def validate_config(config: Config) -> bool:
    """Validate the configuration."""
    if not config.openneuro_dataset_ids:
        raise ValueError("No dataset IDs provided in config.")
    if config.min_age < 0:
        raise ValueError("min_age must be non-negative.")
    if config.max_ram_gb <= 0 or config.max_disk_gb <= 0:
        raise ValueError("Resource limits must be positive.")
    return True
