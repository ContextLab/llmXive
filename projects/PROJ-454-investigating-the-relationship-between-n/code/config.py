"""
Configuration management for the project.

Provides centralized access to configuration values from environment variables,
with defaults and validation.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import json

@dataclass
class Config:
    """Main configuration container."""
    # Data paths
    project_root: Path = Path(__file__).parent.parent
    raw_data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "raw")
    processed_data_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "data" / "processed")
    logs_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent / "logs")
    
    # Dataset configuration
    openneuro_api_url: str = "https://api.openneuro.org"
    dataset_ids: List[str] = field(default_factory=lambda: ["ds003104"])
    wcst_variable_name: str = "wcst_perseverative_errors"
    min_age: int = 50
    
    # Preprocessing parameters
    l_freq: float = 1.0
    h_freq: float = 45.0
    notch_freqs: List[float] = field(default_factory=lambda: [50.0, 60.0])
    bad_channel_threshold: float = 3.0
    n_ica_components: int = 20
    epoch_duration: float = 2.0
    
    # Data quality thresholds
    min_valid_eeg_seconds: int = 60
    max_corrupted_segments_percent: float = 20.0
    min_snr_db: float = 5.0
    
    # Resource limits
    max_memory_gb: float = 7.0
    max_disk_gb: float = 14.0
    
    # Statistical parameters
    vif_threshold: float = 5.0
    fdr_method: str = "benjamini_hochberg"
    
    # Entropy parameters
    sample_entropy_m: int = 2
    sample_entropy_r: float = 0.2
    approximate_entropy_m: int = 2
    approximate_entropy_r: float = 0.2
    
    # Frequency bands (Hz)
    frequency_bands: Dict[str, List[float]] = field(default_factory=lambda: {
        'delta': [0.5, 4.0],
        'theta': [4.0, 8.0],
        'alpha': [8.0, 13.0],
        'beta': [13.0, 30.0],
        'gamma': [30.0, 45.0]
    })
    
    # Power analysis
    power_analysis_deferred: bool = True

_config: Optional[Config] = None

def load_config_from_env() -> Config:
    """Load configuration from environment variables."""
    global _config
    if _config is not None:
        return _config
    
    config = Config()
    
    # Override with environment variables
    if os.getenv('PROJECT_ROOT'):
        config.project_root = Path(os.getenv('PROJECT_ROOT'))
    if os.getenv('RAW_DATA_DIR'):
        config.raw_data_dir = Path(os.getenv('RAW_DATA_DIR'))
    if os.getenv('PROCESSED_DATA_DIR'):
        config.processed_data_dir = Path(os.getenv('PROCESSED_DATA_DIR'))
    if os.getenv('LOGS_DIR'):
        config.logs_dir = Path(os.getenv('LOGS_DIR'))
    if os.getenv('OPENNEURO_API_URL'):
        config.openneuro_api_url = os.getenv('OPENNEURO_API_URL')
    if os.getenv('DATASET_IDS'):
        config.dataset_ids = os.getenv('DATASET_IDS').split(',')
    if os.getenv('WCST_VARIABLE_NAME'):
        config.wcst_variable_name = os.getenv('WCST_VARIABLE_NAME')
    if os.getenv('MIN_AGE'):
        config.min_age = int(os.getenv('MIN_AGE'))
    if os.getenv('L_FREQ'):
        config.l_freq = float(os.getenv('L_FREQ'))
    if os.getenv('H_FREQ'):
        config.h_freq = float(os.getenv('H_FREQ'))
    if os.getenv('NOTCH_FREQS'):
        config.notch_freqs = [float(x) for x in os.getenv('NOTCH_FREQS').split(',')]
    if os.getenv('BAD_CHANNEL_THRESHOLD'):
        config.bad_channel_threshold = float(os.getenv('BAD_CHANNEL_THRESHOLD'))
    if os.getenv('N_ICA_COMPONENTS'):
        config.n_ica_components = int(os.getenv('N_ICA_COMPONENTS'))
    if os.getenv('EPOCH_DURATION'):
        config.epoch_duration = float(os.getenv('EPOCH_DURATION'))
    if os.getenv('MIN_VALID_EEG_SECONDS'):
        config.min_valid_eeg_seconds = int(os.getenv('MIN_VALID_EEG_SECONDS'))
    if os.getenv('MAX_CORRUPTED_PERCENT'):
        config.max_corrupted_segments_percent = float(os.getenv('MAX_CORRUPTED_PERCENT'))
    if os.getenv('MIN_SNR_DB'):
        config.min_snr_db = float(os.getenv('MIN_SNR_DB'))
    if os.getenv('MAX_MEMORY_GB'):
        config.max_memory_gb = float(os.getenv('MAX_MEMORY_GB'))
    if os.getenv('MAX_DISK_GB'):
        config.max_disk_gb = float(os.getenv('MAX_DISK_GB'))
    if os.getenv('VIF_THRESHOLD'):
        config.vif_threshold = float(os.getenv('VIF_THRESHOLD'))
    if os.getenv('FDR_METHOD'):
        config.fdr_method = os.getenv('FDR_METHOD')
    if os.getenv('SAMPLE_ENTROPY_M'):
        config.sample_entropy_m = int(os.getenv('SAMPLE_ENTROPY_M'))
    if os.getenv('SAMPLE_ENTROPY_R'):
        config.sample_entropy_r = float(os.getenv('SAMPLE_ENTROPY_R'))
    if os.getenv('APPROXIMATE_ENTROPY_M'):
        config.approximate_entropy_m = int(os.getenv('APPROXIMATE_ENTROPY_M'))
    if os.getenv('APPROXIMATE_ENTROPY_R'):
        config.approximate_entropy_r = float(os.getenv('APPROXIMATE_ENTROPY_R'))
    if os.getenv('POWER_ANALYSIS_DEFERRED'):
        config.power_analysis_deferred = os.getenv('POWER_ANALYSIS_DEFERRED').lower() in ('true', '1', 'yes')
    
    _config = config
    return config

def validate_config(config: Config) -> bool:
    """Validate configuration values."""
    if config.l_freq >= config.h_freq:
        raise ValueError("l_freq must be less than h_freq")
    if config.min_valid_eeg_seconds <= 0:
        raise ValueError("min_valid_eeg_seconds must be positive")
    if config.min_snr_db <= 0:
        raise ValueError("min_snr_db must be positive")
    return True

def get_config() -> Config:
    """Get the global configuration instance."""
    return load_config_from_env()

def reset_config():
    """Reset the global configuration."""
    global _config
    _config = None

# Convenience functions for specific config values
def get_dataset_url() -> str:
    """Get the OpenNeuro API URL."""
    return get_config().openneuro_api_url

def get_output_path() -> Path:
    """Get the processed data output path."""
    return get_config().processed_data_dir

def get_frequency_band(name: str) -> List[float]:
    """Get frequency band limits."""
    return get_config().frequency_bands.get(name, [0.0, 0.0])

def get_entropy_params() -> Dict[str, Any]:
    """Get entropy calculation parameters."""
    return {
        'sample_entropy': {
            'm': get_config().sample_entropy_m,
            'r': get_config().sample_entropy_r
        },
        'approximate_entropy': {
            'm': get_config().approximate_entropy_m,
            'r': get_config().approximate_entropy_r
        }
    }

def get_data_quality_thresholds() -> Dict[str, Any]:
    """Get data quality thresholds."""
    return {
        'min_valid_eeg_seconds': get_config().min_valid_eeg_seconds,
        'max_corrupted_segments_percent': get_config().max_corrupted_segments_percent,
        'min_snr_db': get_config().min_snr_db
    }

def get_preprocessing_params() -> Dict[str, Any]:
    """Get preprocessing parameters."""
    return {
        'l_freq': get_config().l_freq,
        'h_freq': get_config().h_freq,
        'notch_freqs': get_config().notch_freqs,
        'bad_channel_threshold': get_config().bad_channel_threshold,
        'n_ica_components': get_config().n_ica_components,
        'epoch_duration': get_config().epoch_duration
    }

def get_resource_limits() -> Dict[str, float]:
    """Get resource limits."""
    return {
        'max_memory_gb': get_config().max_memory_gb,
        'max_disk_gb': get_config().max_disk_gb
    }

def get_vif_threshold() -> float:
    """Get VIF threshold."""
    return get_config().vif_threshold

def get_fdr_method() -> str:
    """Get FDR correction method."""
    return get_config().fdr_method

def is_power_analysis_deferred() -> bool:
    """Check if power analysis is deferred."""
    return get_config().power_analysis_deferred

def get_wcst_variable_name() -> str:
    """Get WCST variable name."""
    return get_config().wcst_variable_name

def get_min_age() -> int:
    """Get minimum age threshold."""
    return get_config().min_age

def get_dataset_ids() -> List[str]:
    """Get dataset IDs."""
    return get_config().dataset_ids
