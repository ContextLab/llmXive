"""
Configuration module for the self-improving LLM pipeline.
Defines hyperparameters, safety constraints, and path definitions.
"""
import os
import random
import numpy as np
import torch
from dataclasses import dataclass, field
from typing import List, Optional

# Global configuration instance
_config_instance: Optional['Config'] = None

@dataclass
class Hyperparameters:
    """Hyperparameters for training and evaluation."""
    learning_rate: float = 5e-5
    batch_size: int = 4
    seed: int = 42
    gradient_accumulation_steps: int = 4
    max_epochs: int = 1
    weight_decay: float = 0.01
    warmup_steps: int = 100
    # Bootstrap configuration
    bootstrap_resamples: int = 1000
    bootstrap_alpha: float = 0.05

@dataclass
class SafetyConstraints:
    """Safety and resource constraints."""
    # FR-019: Max parameter increase limit (resolved from [deferred])
    # Set to 30% as per spec requirement
    max_param_increase_percent: float = 0.30
    # SC-005: RAM limit target
    ram_limit_gb: float = 7.0
    # FR-015: Performance degradation threshold for termination
    degradation_threshold: float = 0.05
    # Cycle limits
    max_cycles: int = 3
    max_attempts_per_cycle: int = 3

@dataclass
class PathConfig:
    """Path configuration for the project."""
    # Base directories
    base_dir: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_raw_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw'))
    data_processed_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'processed'))
    results_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results'))
    checkpoints_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'checkpoints'))
    logs_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'logs'))
    
    # Dataset paths (relative to data_raw_dir)
    openwebtext_path: str = "openwebtext"
    gsm8k_path: str = "gsm8k"
    arc_challenge_path: str = "arc_challenge"
    boolq_path: str = "boolq"
    
    # Output paths
    trajectory_path: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'trajectory.json'))
    trade_off_path: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'trade_off_analysis.json'))
    state_path: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'state.json'))

@dataclass
class Config:
    """Main configuration container."""
    hyperparameters: Hyperparameters = field(default_factory=Hyperparameters)
    safety_constraints: SafetyConstraints = field(default_factory=SafetyConstraints)
    paths: PathConfig = field(default_factory=PathConfig)
    
    def set_seed(self):
        """Set random seeds for reproducibility."""
        random.seed(self.hyperparameters.seed)
        np.random.seed(self.hyperparameters.seed)
        torch.manual_seed(self.hyperparameters.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.hyperparameters.seed)

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config_instance
    _config_instance = config

# Convenience accessors
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
    return get_config().safety_constraints.ram_limit_gb

def get_trajectory_path() -> str:
    """Get the trajectory file path from config."""
    return get_config().paths.trajectory_path

def get_max_param_increase_percent() -> float:
    """Get the max parameter increase percentage from config."""
    return get_config().safety_constraints.max_param_increase_percent

def get_bootstrap_resamples() -> int:
    """Get the number of bootstrap resamples from config."""
    return get_config().hyperparameters.bootstrap_resamples

def set_seed(seed: Optional[int] = None) -> None:
    """Set the random seed for reproducibility."""
    if seed is None:
        seed = get_seed()
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    config = get_config()
    dirs = [
        config.paths.data_raw_dir,
        config.paths.data_processed_dir,
        config.paths.results_dir,
        config.paths.checkpoints_dir,
        config.paths.logs_dir,
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

# Initialize config on module load
_config_instance = Config()
ensure_directories()
