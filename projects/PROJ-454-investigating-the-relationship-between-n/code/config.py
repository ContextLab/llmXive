"""
Environment configuration management for dataset URLs and thresholds.

This module provides a centralized configuration system that loads settings
from environment variables or a default configuration. It manages:
- Dataset URLs (OpenNeuro)
- Entropy computation thresholds
- Preprocessing parameters
- Resource limits

All configuration is validated on load to ensure required fields are present.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class Config:
    """
    Centralized configuration container for the project.
    
    Attributes:
        openneuro_base_url: Base URL for OpenNeuro API
        dataset_ids: List of dataset IDs to process (e.g., ds003104)
        wcst_variable: Name of the WCST variable in metadata
        min_age: Minimum participant age for inclusion
        snr_threshold_db: Minimum SNR threshold in dB for data quality
        artifact_threshold_percent: Maximum allowed artifact percentage
        min_eeg_duration_sec: Minimum valid EEG duration in seconds
        max_corrupted_percent: Maximum percentage of corrupted segments allowed
        entropy_method: Entropy method to use ('sample', 'approximate', 'both')
        sample_entropy_m: Sample entropy tolerance parameter
        sample_entropy_r: Sample entropy threshold parameter
        approximate_entropy_m: Approximate entropy embedding dimension
        approximate_entropy_r: Approximate entropy threshold parameter
        frequency_bands: Dict of frequency band names and ranges
        bandpass_low_hz: Lower bound for bandpass filter
        bandpass_high_hz: Upper bound for bandpass filter
        notch_freqs: List of notch filter frequencies
        epoch_duration_sec: Duration of non-overlapping epochs
        output_dirs: Dict of output directory paths
        resource_limits: Dict of resource limits (RAM, disk)
    """
    # Dataset Configuration
    openneuro_base_url: str = "https://api.openneuro.org"
    dataset_ids: List[str] = field(default_factory=lambda: ["ds003104"])
    wcst_variable: str = "wcst_perseverative_errors"
    min_age: int = 50
    
    # Data Quality Thresholds
    snr_threshold_db: float = 5.0
    artifact_threshold_percent: float = 20.0
    min_eeg_duration_sec: float = 60.0
    max_corrupted_percent: float = 20.0
    
    # Entropy Computation Parameters
    entropy_method: str = "both"  # 'sample', 'approximate', 'both'
    sample_entropy_m: int = 2
    sample_entropy_r: float = 0.2
    approximate_entropy_m: int = 2
    approximate_entropy_r: float = 0.2
    
    # Frequency Bands (Hz)
    frequency_bands: Dict[str, List[float]] = field(default_factory=lambda: {
        "delta": [0.5, 4.0],
        "theta": [4.0, 8.0],
        "alpha": [8.0, 13.0],
        "beta": [13.0, 30.0],
        "gamma": [30.0, 45.0]
    })
    
    # Preprocessing Parameters
    bandpass_low_hz: float = 1.0
    bandpass_high_hz: float = 45.0
    notch_freqs: List[float] = field(default_factory=lambda: [50.0, 60.0])
    epoch_duration_sec: float = 2.0
    
    # Output Directories
    output_dirs: Dict[str, str] = field(default_factory=lambda: {
        "raw": "data/raw",
        "processed": "data/processed",
        "interim": "data/interim",
        "logs": "logs",
        "reports": "reports",
        "figures": "figures"
    })
    
    # Resource Limits
    resource_limits: Dict[str, float] = field(default_factory=lambda: {
        "max_ram_gb": 7.0,
        "max_disk_gb": 14.0
    })
    
    # VIF Threshold for Multicollinearity
    vif_threshold: float = 5.0
    
    # FDR Method
    fdr_method: str = "benjamini_hochberg"
    
    # Power Analysis Acknowledgement
    power_analysis_deferred: bool = True

def load_config_from_env(config: Optional[Config] = None) -> Config:
    """
    Load configuration from environment variables, overriding defaults.
    
    Environment variables are prefixed with `LLMXIVE_` for clarity.
    
    Args:
        config: Optional base Config to override. If None, uses defaults.
        
    Returns:
        Config: Updated configuration with environment overrides.
    """
    if config is None:
        config = Config()
    
    # Dataset Configuration
    if os.getenv("LLMXIVE_OPENNEURO_URL"):
        config.openneuro_base_url = os.getenv("LLMXIVE_OPENNEURO_URL")
    
    dataset_ids_env = os.getenv("LLMXIVE_DATASET_IDS")
    if dataset_ids_env:
        config.dataset_ids = [d.strip() for d in dataset_ids_env.split(",")]
    
    if os.getenv("LLMXIVE_WCST_VARIABLE"):
        config.wcst_variable = os.getenv("LLMXIVE_WCST_VARIABLE")
    
    if os.getenv("LLMXIVE_MIN_AGE"):
        config.min_age = int(os.getenv("LLMXIVE_MIN_AGE"))
    
    # Data Quality Thresholds
    if os.getenv("LLMXIVE_SNR_THRESHOLD_DB"):
        config.snr_threshold_db = float(os.getenv("LLMXIVE_SNR_THRESHOLD_DB"))
    
    if os.getenv("LLMXIVE_ARTIFACT_THRESHOLD_PERCENT"):
        config.artifact_threshold_percent = float(os.getenv("LLMXIVE_ARTIFACT_THRESHOLD_PERCENT"))
    
    if os.getenv("LLMXIVE_MIN_EEG_DURATION_SEC"):
        config.min_eeg_duration_sec = float(os.getenv("LLMXIVE_MIN_EEG_DURATION_SEC"))
    
    if os.getenv("LLMXIVE_MAX_CORRUPTED_PERCENT"):
        config.max_corrupted_percent = float(os.getenv("LLMXIVE_MAX_CORRUPTED_PERCENT"))
    
    # Entropy Parameters
    if os.getenv("LLMXIVE_ENTROPY_METHOD"):
        config.entropy_method = os.getenv("LLMXIVE_ENTROPY_METHOD")
    
    if os.getenv("LLMXIVE_SAMPLE_ENTROPY_M"):
        config.sample_entropy_m = int(os.getenv("LLMXIVE_SAMPLE_ENTROPY_M"))
    
    if os.getenv("LLMXIVE_SAMPLE_ENTROPY_R"):
        config.sample_entropy_r = float(os.getenv("LLMXIVE_SAMPLE_ENTROPY_R"))
    
    if os.getenv("LLMXIVE_APPROXIMATE_ENTROPY_M"):
        config.approximate_entropy_m = int(os.getenv("LLMXIVE_APPROXIMATE_ENTROPY_M"))
    
    if os.getenv("LLMXIVE_APPROXIMATE_ENTROPY_R"):
        config.approximate_entropy_r = float(os.getenv("LLMXIVE_APPROXIMATE_ENTROPY_R"))
    
    # Preprocessing Parameters
    if os.getenv("LLMXIVE_BANDPASS_LOW_HZ"):
        config.bandpass_low_hz = float(os.getenv("LLMXIVE_BANDPASS_LOW_HZ"))
    
    if os.getenv("LLMXIVE_BANDPASS_HIGH_HZ"):
        config.bandpass_high_hz = float(os.getenv("LLMXIVE_BANDPASS_HIGH_HZ"))
    
    if os.getenv("LLMXIVE_NOTCH_FREQS"):
        config.notch_freqs = [float(f) for f in os.getenv("LLMXIVE_NOTCH_FREQS").split(",")]
    
    if os.getenv("LLMXIVE_EPOCH_DURATION_SEC"):
        config.epoch_duration_sec = float(os.getenv("LLMXIVE_EPOCH_DURATION_SEC"))
    
    # VIF and FDR
    if os.getenv("LLMXIVE_VIF_THRESHOLD"):
        config.vif_threshold = float(os.getenv("LLMXIVE_VIF_THRESHOLD"))
    
    if os.getenv("LLMXIVE_FDR_METHOD"):
        config.fdr_method = os.getenv("LLMXIVE_FDR_METHOD")
    
    return config

def validate_config(config: Config) -> bool:
    """
    Validate that all required configuration values are present and reasonable.
    
    Args:
        config: Config instance to validate
        
    Returns:
        bool: True if valid, raises ValueError otherwise
        
    Raises:
        ValueError: If any required field is missing or invalid
    """
    # Validate dataset IDs
    if not config.dataset_ids:
        raise ValueError("At least one dataset ID must be specified")
    
    for ds_id in config.dataset_ids:
        if not ds_id.startswith("ds"):
            raise ValueError(f"Invalid dataset ID format: {ds_id}. Must start with 'ds'")
    
    # Validate thresholds
    if config.snr_threshold_db < 0:
        raise ValueError(f"SNR threshold must be non-negative: {config.snr_threshold_db}")
    
    if config.artifact_threshold_percent < 0 or config.artifact_threshold_percent > 100:
        raise ValueError(f"Artifact threshold must be between 0 and 100: {config.artifact_threshold_percent}")
    
    if config.min_eeg_duration_sec <= 0:
        raise ValueError(f"Minimum EEG duration must be positive: {config.min_eeg_duration_sec}")
    
    if config.max_corrupted_percent < 0 or config.max_corrupted_percent > 100:
        raise ValueError(f"Max corrupted percent must be between 0 and 100: {config.max_corrupted_percent}")
    
    # Validate entropy parameters
    if config.sample_entropy_m <= 0:
        raise ValueError(f"Sample entropy m must be positive: {config.sample_entropy_m}")
    
    if config.sample_entropy_r <= 0:
        raise ValueError(f"Sample entropy r must be positive: {config.sample_entropy_r}")
    
    if config.approximate_entropy_m <= 0:
        raise ValueError(f"Approximate entropy m must be positive: {config.approximate_entropy_m}")
    
    if config.approximate_entropy_r <= 0:
        raise ValueError(f"Approximate entropy r must be positive: {config.approximate_entropy_r}")
    
    # Validate frequency bands
    for band_name, (low, high) in config.frequency_bands.items():
        if low >= high:
            raise ValueError(f"Invalid frequency band {band_name}: low ({low}) >= high ({high})")
        if low < 0:
            raise ValueError(f"Invalid frequency band {band_name}: low ({low}) < 0")
    
    # Validate preprocessing parameters
    if config.bandpass_low_hz <= 0:
        raise ValueError(f"Bandpass low must be positive: {config.bandpass_low_hz}")
    
    if config.bandpass_high_hz <= config.bandpass_low_hz:
        raise ValueError(f"Bandpass high ({config.bandpass_high_hz}) must be > low ({config.bandpass_low_hz})")
    
    if config.epoch_duration_sec <= 0:
        raise ValueError(f"Epoch duration must be positive: {config.epoch_duration_sec}")
    
    # Validate VIF threshold
    if config.vif_threshold <= 0:
        raise ValueError(f"VIF threshold must be positive: {config.vif_threshold}")
    
    # Validate FDR method
    valid_fdr_methods = ["benjamini_hochberg", "benjamini_yekutieli", "storey"]
    if config.fdr_method not in valid_fdr_methods:
        raise ValueError(f"Invalid FDR method: {config.fdr_method}. Must be one of {valid_fdr_methods}")
    
    # Validate resource limits
    if config.resource_limits["max_ram_gb"] <= 0:
        raise ValueError(f"Max RAM must be positive: {config.resource_limits['max_ram_gb']}")
    
    if config.resource_limits["max_disk_gb"] <= 0:
        raise ValueError(f"Max disk must be positive: {config.resource_limits['max_disk_gb']}")
    
    return True

# Global config instance
_config: Optional[Config] = None

def get_config() -> Config:
    """
    Get the global configuration instance, loading from environment if not yet loaded.
    
    Returns:
        Config: The global configuration instance
    """
    global _config
    if _config is None:
        _config = load_config_from_env(Config())
        validate_config(_config)
    return _config

def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _config
    _config = None

def get_dataset_url(dataset_id: str) -> str:
    """
    Construct the full URL for a dataset on OpenNeuro.
    
    Args:
        dataset_id: The dataset ID (e.g., 'ds003104')
        
    Returns:
        str: Full URL to the dataset
    """
    config = get_config()
    return f"{config.openneuro_base_url}/datasets/{dataset_id}"

def get_output_path(output_type: str, filename: str) -> Path:
    """
    Construct the full path for an output file.
    
    Args:
        output_type: One of 'raw', 'processed', 'interim', 'logs', 'reports', 'figures'
        filename: Name of the file
        
    Returns:
        Path: Full path to the output file
    """
    config = get_config()
    base_dir = Path(config.output_dirs[output_type])
    return base_dir / filename

def get_frequency_band(band_name: str) -> List[float]:
    """
    Get the frequency range for a named band.
    
    Args:
        band_name: Name of the frequency band (delta, theta, alpha, beta, gamma)
        
    Returns:
        List[float]: [low_hz, high_hz] for the band
    """
    config = get_config()
    if band_name not in config.frequency_bands:
        raise ValueError(f"Unknown frequency band: {band_name}")
    return config.frequency_bands[band_name]

def get_entropy_params() -> Dict[str, Any]:
    """
    Get entropy computation parameters.
    
    Returns:
        Dict containing method and parameters for entropy calculation
    """
    config = get_config()
    return {
        "method": config.entropy_method,
        "sample_entropy": {
            "m": config.sample_entropy_m,
            "r": config.sample_entropy_r
        },
        "approximate_entropy": {
            "m": config.approximate_entropy_m,
            "r": config.approximate_entropy_r
        }
    }

def get_data_quality_thresholds() -> Dict[str, float]:
    """
    Get all data quality thresholds.
    
    Returns:
        Dict containing all data quality thresholds
    """
    config = get_config()
    return {
        "snr_threshold_db": config.snr_threshold_db,
        "artifact_threshold_percent": config.artifact_threshold_percent,
        "min_eeg_duration_sec": config.min_eeg_duration_sec,
        "max_corrupted_percent": config.max_corrupted_percent
    }

def get_preprocessing_params() -> Dict[str, Any]:
    """
    Get preprocessing parameters.
    
    Returns:
        Dict containing all preprocessing parameters
    """
    config = get_config()
    return {
        "bandpass_low_hz": config.bandpass_low_hz,
        "bandpass_high_hz": config.bandpass_high_hz,
        "notch_freqs": config.notch_freqs,
        "epoch_duration_sec": config.epoch_duration_sec
    }

def get_resource_limits() -> Dict[str, float]:
    """
    Get resource limits.
    
    Returns:
        Dict containing RAM and disk limits
    """
    config = get_config()
    return config.resource_limits

def get_vif_threshold() -> float:
    """
    Get the VIF threshold for multicollinearity detection.
    
    Returns:
        float: VIF threshold value
    """
    return get_config().vif_threshold

def get_fdr_method() -> str:
    """
    Get the FDR correction method.
    
    Returns:
        str: FDR method name
    """
    return get_config().fdr_method

def is_power_analysis_deferred() -> bool:
    """
    Check if power analysis sample size requirements are deferred.
    
    Returns:
        bool: True if deferred
    """
    return get_config().power_analysis_deferred

def get_wcst_variable_name() -> str:
    """
    Get the name of the WCST variable in the dataset.
    
    Returns:
        str: WCST variable name
    """
    return get_config().wcst_variable

def get_min_age() -> int:
    """
    Get the minimum participant age for inclusion.
    
    Returns:
        int: Minimum age
    """
    return get_config().min_age

def get_dataset_ids() -> List[str]:
    """
    Get the list of dataset IDs to process.
    
    Returns:
        List[str]: Dataset IDs
    """
    return get_config().dataset_ids
