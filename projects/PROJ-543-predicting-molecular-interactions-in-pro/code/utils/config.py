"""
Environment configuration management for the Molecular Interactions project.
Handles seeds, hyperparameters, and environment variables for reproducibility.
"""
import os
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import numpy as np
import torch

@dataclass
class Hyperparameters:
    """Configuration for model hyperparameters."""
    learning_rate: float = 1e-3
    batch_size: int = 32
    num_epochs: int = 50
    hidden_channels: int = 128
    num_layers: int = 3
    dropout: float = 0.1
    patience: int = 10  # For early stopping
    cutoff_distance: float = 5.0  # Angstroms for edge construction
    water_cutoff: float = 3.5  # Angstroms for water-mediated interactions
    resolution_threshold: float = 2.5  # Angstroms, max allowed
    max_runtime_hours: float = 4.0  # For training
    timeout_hours: float = 3.5  # For data ingestion
    fdr_alpha: float = 0.05
    t_test_alpha: float = 0.05
    min_samples_dbscan: int = 5
    rmsd_threshold: float = 1.5  # Angstroms for pharmacophore matching

@dataclass
class EnvironmentConfig:
    """Global environment configuration."""
    project_root: str = "projects/PROJ-543-predicting-molecular-interactions-in-pro"
    data_raw_dir: str = "data/raw"
    data_processed_dir: str = "data/processed"
    data_results_dir: str = "data/results"
    data_reference_dir: str = "data/reference"
    code_dir: str = "code"
    specs_dir: str = "specs"
    tests_dir: str = "tests"
    log_level: str = "INFO"
    seed: int = 42
    use_cuda: bool = True
    memory_limit_gb: float = 7.0
    device: Optional[str] = None

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility across all libraries."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

def get_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables or return defaults.
    Returns a dictionary containing both Hyperparameters and EnvironmentConfig.
    """
    # Load hyperparameters from env if set, otherwise use defaults
    hp = Hyperparameters(
        learning_rate=float(os.getenv("LEARNING_RATE", 1e-3)),
        batch_size=int(os.getenv("BATCH_SIZE", 32)),
        num_epochs=int(os.getenv("NUM_EPOCHS", 50)),
        hidden_channels=int(os.getenv("HIDDEN_CHANNELS", 128)),
        num_layers=int(os.getenv("NUM_LAYERS", 3)),
        dropout=float(os.getenv("DROPOUT", 0.1)),
        patience=int(os.getenv("PATIENCE", 10)),
        cutoff_distance=float(os.getenv("CUTOFF_DISTANCE", 5.0)),
        water_cutoff=float(os.getenv("WATER_CUTOFF", 3.5)),
        resolution_threshold=float(os.getenv("RESOLUTION_THRESHOLD", 2.5)),
        max_runtime_hours=float(os.getenv("MAX_RUNTIME_HOURS", 4.0)),
        timeout_hours=float(os.getenv("TIMEOUT_HOURS", 3.5)),
        fdr_alpha=float(os.getenv("FDR_ALPHA", 0.05)),
        t_test_alpha=float(os.getenv("T_TEST_ALPHA", 0.05)),
        min_samples_dbscan=int(os.getenv("MIN_SAMPLES_DBSCAN", 5)),
        rmsd_threshold=float(os.getenv("RMSD_THRESHOLD", 1.5)),
    )

    # Load environment config
    env_cfg = EnvironmentConfig(
        project_root=os.getenv("PROJECT_ROOT", "projects/PROJ-543-predicting-molecular-interactions-in-pro"),
        data_raw_dir=os.getenv("DATA_RAW_DIR", "data/raw"),
        data_processed_dir=os.getenv("DATA_PROCESSED_DIR", "data/processed"),
        data_results_dir=os.getenv("DATA_RESULTS_DIR", "data/results"),
        data_reference_dir=os.getenv("DATA_REFERENCE_DIR", "data/reference"),
        code_dir=os.getenv("CODE_DIR", "code"),
        specs_dir=os.getenv("_SPECS_DIR", "specs"),
        tests_dir=os.getenv("TESTS_DIR", "tests"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        seed=int(os.getenv("RANDOM_SEED", 42)),
        use_cuda=os.getenv("USE_CUDA", "1") in ["1", "true", "True", "yes"],
        memory_limit_gb=float(os.getenv("MEMORY_LIMIT_GB", 7.0)),
    )

    # Determine device
    if env_cfg.use_cuda and torch.cuda.is_available():
        env_cfg.device = "cuda"
    else:
        env_cfg.device = "cpu"

    return {
        "hyperparameters": hp,
        "environment": env_cfg,
    }

def load_config_from_env() -> Dict[str, Any]:
    """
    Alias for get_config() to ensure consistent API usage.
    Loads configuration from environment variables.
    """
    return get_config()

def initialize_environment() -> Dict[str, Any]:
    """
    Initialize the environment by setting seeds and loading configuration.
    Returns the full configuration dictionary.
    """
    config = get_config()
    set_seed(config["environment"].seed)
    return config