import os
import random
import numpy as np
import torch
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Hyperparameters:
    """Hyperparameters for training and evaluation."""
    learning_rate: float = 5e-5
    batch_size: int = 4
    seed: int = 42
    gradient_accumulation_steps: int = 4
    max_epochs: int = 1
    weight_decay: float = 0.01
    warmup_ratio: float = 0.03
    bootstrap_resamples: int = 1000


@dataclass
class SafetyConstraints:
    """Safety and resource constraints."""
    # Placeholder for param increase limit; to be resolved in research phase.
    # FR-021 and T059 enforce a 30% hard limit at runtime.
    param_increase_limit_percent: float = 30.0
    ram_limit_gb: float = 7.0
    max_cycle_attempts: int = 3
    early_stop_degradation_threshold: float = 0.05  # 5% degradation


@dataclass
class PathConfig:
    """Path definitions for project artifacts."""
    base_dir: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_raw_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw"))
    data_processed_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed"))
    results_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results"))
    specs_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "specs"))
    checkpoints_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "checkpoints"))
    trajectory_path: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "trajectory.json"))
    trade_off_path: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "trade_off_analysis.json"))
    state_path: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "state.json"))
    logs_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "logs"))


@dataclass
class Config:
    """Master configuration holding all settings."""
    hyperparameters: Hyperparameters = field(default_factory=Hyperparameters)
    safety: SafetyConstraints = field(default_factory=SafetyConstraints)
    paths: PathConfig = field(default_factory=PathConfig)


_global_config: Optional[Config] = None


def get_config() -> Config:
    """Returns the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def set_config(config: Config) -> None:
    """Sets the global configuration instance."""
    global _global_config
    _global_config = config


# --- Convenience getters ---


def get_learning_rate() -> float:
    return get_config().hyperparameters.learning_rate


def get_batch_size() -> int:
    return get_config().hyperparameters.batch_size


def get_seed() -> int:
    return get_config().hyperparameters.seed


def get_ram_limit() -> float:
    return get_config().safety.ram_limit_gb


def get_trajectory_path() -> str:
    return get_config().paths.trajectory_path


def get_max_param_increase_percent() -> float:
    return get_config().safety.param_increase_limit_percent


def get_bootstrap_resamples() -> int:
    return get_config().hyperparameters.bootstrap_resamples


def set_seed(seed: Optional[int] = None) -> None:
    """Sets the random seed for reproducibility."""
    if seed is None:
        seed = get_seed()
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def ensure_directories() -> None:
    """Creates all required directories defined in PathConfig."""
    cfg = get_config().paths
    dirs = [
        cfg.data_raw_dir,
        cfg.data_processed_dir,
        cfg.results_dir,
        cfg.specs_dir,
        cfg.checkpoints_dir,
        cfg.logs_dir,
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
