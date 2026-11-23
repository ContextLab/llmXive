"""
Configuration management for the neural entropy project.
Provides centralized configuration with environment variable support.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import json

# ----------------------------------------------------------------------
# Module‑level constants required by task T008
# ----------------------------------------------------------------------
# These constants must be importable directly from the config module.
OPENNEURO_DATASET_IDS = ["ds000246", "ds003104"]
SNR_THRESHOLD = 5.0
ARTIFACT_THRESHOLD = 0.2
SEED = 42

@dataclass
class Config:
    """Main configuration dataclass."""
    # Dataset configuration
    OPENNEURO_DATASET_IDS: List[str] = field(
        default_factory=lambda: ["ds000246", "ds003104"]
    )

    # Thresholds
    SNR_THRESHOLD: float = 5.0  # dB
    ARTIFACT_THRESHOLD: float = 0.2  # microvolts (as per T008)

    # Random seed for reproducibility
    SEED: int = 42

    # Paths
    RAW_DATA_DIR: Path = Path("data/raw")
    PROCESSED_DATA_DIR: Path = Path("data/processed")
    INTERIM_DATA_DIR: Path = Path("data/interim")
    LOGS_DIR: Path = Path("logs")
    REPORTS_DIR: Path = Path("reports")

    # Processing parameters
    FREQUENCY_BANDS: Dict[str, tuple] = field(
        default_factory=lambda: {
            "delta": (1, 4),
            "theta": (4, 8),
            "alpha": (8, 13),
            "beta": (13, 30),
            "gamma": (30, 45),
        }
    )

    # Entropy parameters
    SAMPLE_ENTROPY_M: int = 2
    SAMPLE_ENTROPY_R: float = 0.2
    APPROXIMATE_ENTROPY_M: int = 2
    APPROXIMATE_ENTROPY_R: float = 0.2

    # Resource limits
    MAX_MEMORY_GB: float = 7.0
    MAX_DISK_GB: float = 14.0

    # Statistical parameters
    VIF_THRESHOLD: float = 5.0
    FDR_METHOD: str = "benjamini_hochberg"

    # Behavioral data
    WCST_VARIABLE_NAME: str = "wcst_perseverative_errors"
    MIN_AGE: int = 18

    # Power analysis
    POWER_ANALYSIS_DEFERRED: bool = True

_config: Optional[Config] = None

def load_config_from_env() -> Config:
    """Load configuration from environment variables with defaults."""
    global _config

    dataset_ids_str = os.getenv(
        "OPENNEURO_DATASET_IDS", "ds000246,ds003104"
    )
    dataset_ids = [
        id_.strip() for id_ in dataset_ids_str.split(",") if id_.strip()
    ]

    snr_threshold = float(os.getenv("SNR_THRESHOLD", "5.0"))
    artifact_threshold = float(os.getenv("ARTIFACT_THRESHOLD", "0.2"))
    seed = int(os.getenv("SEED", "42"))

    config = Config(
        OPENNEURO_DATASET_IDS=dataset_ids,
        SNR_THRESHOLD=snr_threshold,
        ARTIFACT_THRESHOLD=artifact_threshold,
        SEED=seed,
    )

    _config = config
    return config


def validate_config(config: Config) -> bool:
    """Validate configuration values."""
    if not config.OPENNEURO_DATASET_IDS:
        raise ValueError("OPENNEURO_DATASET_IDS cannot be empty")
    if config.SNR_THRESHOLD <= 0:
        raise ValueError("SNR_THRESHOLD must be positive")
    if config.SEED < 0:
        raise ValueError("SEED must be non-negative")
    return True


def get_config() -> Config:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config_from_env()
    return _config


def reset_config():
    """Reset the global configuration."""
    global _config
    _config = None


def get_dataset_ids() -> List[str]:
    """Get the list of dataset IDs to process."""
    return get_config().OPENNEURO_DATASET_IDS


def get_output_path(data_type: str, filename: str) -> Path:
    """Get output path for a specific data type."""
    config = get_config()
    if data_type == "raw":
        return config.RAW_DATA_DIR / filename
    elif data_type == "processed":
        return config.PROCESSED_DATA_DIR / filename
    elif data_type == "interim":
        return config.INTERIM_DATA_DIR / filename
    else:
        raise ValueError(f"Unknown data type: {data_type}")


def get_frequency_band(band_name: str) -> tuple:
    """Get frequency range for a named band."""
    return get_config().FREQUENCY_BANDS[band_name]


def get_entropy_params() -> Dict[str, Any]:
    """Get entropy calculation parameters."""
    config = get_config()
    return {
        "sample_entropy_m": config.SAMPLE_ENTROPY_M,
        "sample_entropy_r": config.SAMPLE_ENTROPY_R,
        "approximate_entropy_m": config.APPROXIMATE_ENTROPY_M,
        "approximate_entropy_r": config.APPROXIMATE_ENTROPY_R,
    }


def get_data_quality_thresholds() -> Dict[str, float]:
    """Get data quality thresholds."""
    config = get_config()
    return {
        "snr_threshold": config.SNR_THRESHOLD,
        "artifact_threshold": config.ARTIFACT_THRESHOLD,
    }


def get_preprocessing_params() -> Dict[str, Any]:
    """Get preprocessing parameters."""
    config = get_config()
    return {
        "frequency_bands": config.FREQUENCY_BANDS,
        "seed": config.SEED,
    }


def get_resource_limits() -> Dict[str, float]:
    """Get resource limits."""
    config = get_config()
    return {
        "max_memory_gb": config.MAX_MEMORY_GB,
        "max_disk_gb": config.MAX_DISK_GB,
    }


def get_vif_threshold() -> float:
    """Get VIF threshold for multicollinearity check."""
    return get_config().VIF_THRESHOLD


def get_fdr_method() -> str:
    """Get FDR correction method."""
    return get_config().FDR_METHOD


def is_power_analysis_deferred() -> bool:
    """Check if power analysis is deferred."""
    return get_config().POWER_ANALYSIS_DEFERRED


def get_wcst_variable_name() -> str:
    """Get the WCST variable name."""
    return get_config().WCST_VARIABLE_NAME


def get_min_age() -> int:
    """Get minimum age threshold."""
    return get_config().MIN_AGE


def get_dataset_url(dataset_id: str) -> str:
    """Get HuggingFace URL for a dataset."""
    return f"https://huggingface.co/datasets/{dataset_id}"