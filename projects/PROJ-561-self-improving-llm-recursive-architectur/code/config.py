import os
from dataclasses import dataclass, field
from typing import List, Optional
import random
import numpy as np
import torch

@dataclass
class Hyperparameters:
    """Core training hyperparameters."""
    learning_rate: float = 5e-5
    
    # Batch size (FIXED at 4 per FR-004, no auto-scaling)
    batch_size: int = 4
    
    # Random seed for reproducibility
    seed: int = 42
    gradient_accumulation_steps: int = 4
    max_epochs: int = 1
    weight_decay: float = 0.01
    warmup_steps: int = 100

    def set_seed(self):
        """Set all random seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)

@dataclass
class SafetyConstraints:
    """Safety and resource constraints for the recursive loop."""
    max_param_increase_percent: float = 30.0
    max_ram_gb: float = 7.0
    max_training_time_hours: float = 6.0
    max_cycle_timeout_seconds: int = 3600
    early_stop_degradation_threshold: float = 0.05
    max_retries: int = 2

@dataclass
class PathConfig:
    """Project path definitions."""
    root: str = field(default_factory=lambda: os.getcwd())
    code_dir: str = "code"
    data_raw_dir: str = "data/raw"
    data_processed_dir: str = "data/processed"
    results_dir: str = "results"
    specs_dir: str = "specs"
    tests_dir: str = "tests"
    figures_dir: str = "figures"
    checkpoints_dir: str = "data/checkpoints"
    logs_dir: str = "results/logs"
    trajectory_file: str = "results/trajectory.json"
    trade_off_file: str = "results/trade_off_analysis.json"

    def __post_init__(self):
        """Ensure required directories exist."""
        dirs = [
            self.data_raw_dir,
            self.data_processed_dir,
            self.results_dir,
            self.specs_dir,
            self.tests_dir,
            self.figures_dir,
            self.checkpoints_dir,
            self.logs_dir
        ]
        for d in dirs:
            os.makedirs(os.path.join(self.root, d), exist_ok=True)

    @property
    def trajectory_path(self) -> str:
        return os.path.join(self.root, self.trajectory_file)

    @property
    def trade_off_path(self) -> str:
        return os.path.join(self.root, self.trade_off_file)

    @property
    def checkpoints_path(self) -> str:
        return os.path.join(self.root, self.checkpoints_dir)

    @property
    def logs_path(self) -> str:
        return os.path.join(self.root, self.logs_dir)

def get_config_summary() -> dict:
    """Return a dictionary summary of current configuration."""
    hp = Hyperparameters()
    sc = SafetyConstraints()
    pc = PathConfig()
    return {
        "hyperparameters": {
            "learning_rate": hp.learning_rate,
            "batch_size": hp.batch_size,
            "seed": hp.seed,
            "gradient_accumulation_steps": hp.gradient_accumulation_steps
        },
        "constraints": {
            "max_param_increase_percent": sc.max_param_increase_percent,
            "max_ram_gb": sc.max_ram_gb,
            "max_training_time_hours": sc.max_training_time_hours
        },
        "paths": {
            "data_raw": pc.data_raw_dir,
            "data_processed": pc.data_processed_dir,
            "results": pc.results_dir,
            "checkpoints": pc.checkpoints_dir
        }


def get_config_summary() -> dict:
    """Get a summary of the default configuration."""
    config = Config()
    return config.summary()


# Global default configuration instance
_default_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global default configuration."""
    global _default_config
    if _default_config is None:
        _default_config = Config()
    return _default_config


def set_config(config: Config):
    """Set the global configuration."""
    global _default_config
    _default_config = config