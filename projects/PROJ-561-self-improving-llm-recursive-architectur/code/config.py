"""
Central configuration module for the self-improving LLM pipeline.
Defines hyperparameters, safety constraints, and path definitions.
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional
import random
import numpy as np
import torch


@dataclass
class Hyperparameters:
    """Training and optimization hyperparameters."""
    learning_rate: float = 5e-5
    batch_size: int = 4
    seed: int = 42
    gradient_accumulation_steps: int = 4
    max_epochs: int = 1
    weight_decay: float = 0.01
    warmup_steps: int = 100
    max_grad_norm: float = 1.0


@dataclass
class SafetyConstraints:
    """Safety and resource constraints for the recursive loop."""
    max_param_increase_pct: float = 0.30  # ≤30% parameter increase allowed
    max_ram_gb: float = 7.0
    max_training_time_seconds: int = 5400  # 1.5 hours per cycle
    early_stop_degradation_pct: float = 0.05  # 5% degradation triggers early stop
    max_training_retries: int = 2


@dataclass
class PathConfig:
    """File system paths for project artifacts."""
    project_root: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    code_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    data_raw_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw'))
    data_processed_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'processed'))
    results_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results'))
    logs_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'logs'))
    checkpoints_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'checkpoints'))
    specs_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'specs'))
    templates_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates'))
    trajectory_path: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'trajectory.json'))
    state_path: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'state.json'))
    decay_summary_path: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'decay_summary.json'))
    trade_off_path: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'trade_off_analysis.json'))


@dataclass
class Config:
    """Master configuration combining all settings."""
    hyperparameters: Hyperparameters = field(default_factory=Hyperparameters)
    safety: SafetyConstraints = field(default_factory=SafetyConstraints)
    paths: PathConfig = field(default_factory=PathConfig)


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Retrieve the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(new_config: Config) -> None:
    """Update the global configuration instance."""
    global _config
    _config = new_config


def get_learning_rate() -> float:
    """Convenience accessor for learning rate."""
    return get_config().hyperparameters.learning_rate


def get_batch_size() -> int:
    """Convenience accessor for batch size."""
    return get_config().hyperparameters.batch_size


def get_seed() -> int:
    """Convenience accessor for random seed."""
    return get_config().hyperparameters.seed


def get_ram_limit() -> float:
    """Convenience accessor for RAM limit in GB."""
    return get_config().safety.max_ram_gb


def get_trajectory_path() -> str:
    """Convenience accessor for trajectory file path."""
    return get_config().paths.trajectory_path


def set_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility across all libraries."""
    if seed is None:
        seed = get_seed()
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def ensure_directories() -> None:
    """Create all required directories if they do not exist."""
    config = get_config()
    dirs = [
        config.paths.data_raw_dir,
        config.paths.data_processed_dir,
        config.paths.results_dir,
        config.paths.logs_dir,
        config.paths.checkpoints_dir,
        config.paths.specs_dir,
        config.paths.templates_dir,
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)