import os
import random
import numpy as np
import torch
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Hyperparameters:
    """Core training hyperparameters."""
    learning_rate: float = 5e-5
    batch_size: int = 4
    seed: int = 42
    num_epochs: int = 1
    max_tokens: int = 512
    warmup_steps: int = 100
    weight_decay: float = 0.01
    gradient_accumulation_steps: int = 1
    dropout: float = 0.1

@dataclass
class SafetyConstraints:
    """Safety and resource constraints."""
    param_limit_percent: float = 0.30  # Max 30% parameter increase
    ram_limit_gb: float = 7.0
    max_cycles: int = 3
    max_retries_per_cycle: int = 2
    timeout_seconds: int = 3600
    early_stop_threshold: float = 0.05  # 5% degradation threshold

@dataclass
class PathConfig:
    """Project path definitions."""
    root: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_raw: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw"))
    data_processed: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "processed"))
    results: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results"))
    specs: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "specs"))
    logs: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"))
    state: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "state"))
    trajectory: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "trajectory.json"))
    final_report: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "final_report.md"))

@dataclass
class Config:
    """Master configuration container."""
    hyperparameters: Hyperparameters = field(default_factory=Hyperparameters)
    safety: SafetyConstraints = field(default_factory=SafetyConstraints)
    paths: PathConfig = field(default_factory=PathConfig)

# Global config instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Return the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def set_config(cfg: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = cfg

# Convenience getters
def get_learning_rate() -> float:
    return get_config().hyperparameters.learning_rate

def get_batch_size() -> int:
    return get_config().hyperparameters.batch_size

def get_seed() -> int:
    return get_config().hyperparameters.seed

def get_ram_limit() -> float:
    return get_config().safety.ram_limit_gb

def get_trajectory_path() -> str:
    return get_config().paths.trajectory

def get_max_param_increase_percent() -> float:
    return get_config().safety.param_limit_percent

def get_bootstrap_resamples() -> int:
    return 1000

def set_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = get_seed()
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    cfg = get_config()
    dirs = [
        cfg.paths.data_raw,
        cfg.paths.data_processed,
        cfg.paths.results,
        cfg.paths.specs,
        cfg.paths.logs,
        cfg.paths.state,
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

# Verification asserts for T008
if __name__ == "__main__":
    cfg = get_config()
    assert cfg.hyperparameters.learning_rate == 5e-5, "Learning rate must be 5e-5"
    assert cfg.hyperparameters.batch_size == 4, "Batch size must be 4"
    assert cfg.hyperparameters.seed == 42, "Seed must be 42"
    assert cfg.safety.param_limit_percent == 0.30, "Param limit must be 30%"
    assert cfg.safety.ram_limit_gb == 7.0, "RAM limit must be 7GB"
    assert os.path.isabs(cfg.paths.root) or cfg.paths.root.endswith("code"), "Root path must be valid"
    print("Config verification passed.")
    ensure_directories()
    print(f"Directories created: {cfg.paths.results}, {cfg.paths.data_raw}")