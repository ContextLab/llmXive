import os
from dataclasses import dataclass, field
from typing import List, Optional
import random
import numpy as np
import torch

@dataclass
class Hyperparameters:
    learning_rate: float = 5e-5
    batch_size: int = 4
    seed: int = 42
    gradient_accumulation_steps: int = 4
    max_epochs: int = 10
    timeout_per_cycle: int = 3600  # 1 hour in seconds

@dataclass
class SafetyConstraints:
    max_param_increase: float = 0.3  # 30% increase
    max_ram_gb: float = 7.0
    early_stop_degradation: float = 0.05  # 5% degradation
    max_attempts: int = 3

@dataclass
class PathConfig:
    project_root: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir: str = "data"
    results_dir: str = "results"
    checkpoints_dir: str = "data/checkpoints"
    logs_dir: str = "results/logs"
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"

@dataclass
class Config:
    hyperparameters: Hyperparameters = field(default_factory=Hyperparameters)
    safety: SafetyConstraints = field(default_factory=SafetyConstraints)
    paths: PathConfig = field(default_factory=PathConfig)

_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def set_config(config: Config) -> None:
    """Set the global configuration."""
    global _config
    _config = config

def get_learning_rate() -> float:
    """Get the learning rate from config."""
    return get_config().hyperparameters.learning_rate

def get_batch_size() -> int:
    """Get the batch size from config."""
    return get_config().hyperparameters.batch_size

def get_seed() -> int:
    """Get the random seed from config."""
    return get_config().hyperparameters.seed

def get_ram_limit() -> float:
    """Get the RAM limit in GB from config."""
    return get_config().safety.max_ram_gb

def get_trajectory_path() -> str:
    """Get the path to the trajectory file."""
    config = get_config()
    return os.path.join(config.paths.results_dir, "trajectory.json")

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    config = get_config()
    os.makedirs(config.paths.data_dir, exist_ok=True)
    os.makedirs(config.paths.results_dir, exist_ok=True)
    os.makedirs(config.paths.checkpoints_dir, exist_ok=True)
    os.makedirs(config.paths.logs_dir, exist_ok=True)
    os.makedirs(config.paths.raw_data_dir, exist_ok=True)
    os.makedirs(config.paths.processed_data_dir, exist_ok=True)