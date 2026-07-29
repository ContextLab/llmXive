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
    batch_size: int = 4
    seed: int = 42
    gradient_accumulation_steps: int = 4
    max_epochs: int = 1
    weight_decay: float = 0.01
    warmup_steps: int = 100
    max_grad_norm: float = 1.0

@dataclass
class SafetyConstraints:
    """Safety and resource constraints."""
    max_param_increase_percent: float = 30.0
    ram_limit_gb: float = 7.0
    degradation_threshold_percent: float = 5.0
    max_cycles: int = 10
    timeout_seconds: int = 3600
    max_prompt_attempts: int = 3
    max_training_retries: int = 2

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
    templates_dir: str = "templates"
    checkpoints_dir: str = "data/checkpoints"
    logs_dir: str = "results/logs"
    trajectory_file: str = "results/trajectory.json"
    decay_analysis_file: str = "results/decay_analysis.json"
    trade_off_file: str = "results/trade_off_analysis.json"
    state_file: str = "results/state.json"

    def __post_init__(self):
        # Ensure paths are relative to root if not absolute
        if not os.path.isabs(self.root):
            self.root = os.path.abspath(self.root)
        
        # Construct full paths
        self.data_raw_path = os.path.join(self.root, self.data_raw_dir)
        self.data_processed_path = os.path.join(self.root, self.data_processed_dir)
        self.results_path = os.path.join(self.root, self.results_dir)
        self.checkpoints_path = os.path.join(self.root, self.checkpoints_dir)
        self.logs_path = os.path.join(self.root, self.logs_dir)

@dataclass
class Config:
    """Master configuration container."""
    hyperparameters: Hyperparameters = field(default_factory=Hyperparameters)
    safety: SafetyConstraints = field(default_factory=SafetyConstraints)
    paths: PathConfig = field(default_factory=PathConfig)

_global_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _global_config
    _global_config = config

def get_learning_rate() -> float:
    """Get the current learning rate."""
    return get_config().hyperparameters.learning_rate

def get_batch_size() -> int:
    """Get the current batch size."""
    return get_config().hyperparameters.batch_size

def get_seed() -> int:
    """Get the random seed."""
    return get_config().hyperparameters.seed

def get_ram_limit() -> float:
    """Get the RAM limit in GB."""
    return get_config().safety.ram_limit_gb

def get_trajectory_path() -> str:
    """Get the path to the trajectory file."""
    return os.path.join(get_config().paths.root, get_config().paths.trajectory_file)

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
    config = get_config()
    dirs_to_create = [
        config.paths.data_raw_path,
        config.paths.data_processed_path,
        config.paths.results_path,
        config.paths.checkpoints_path,
        config.paths.logs_path,
        config.paths.specs_dir if not os.path.isabs(config.paths.specs_dir) else config.paths.specs_dir,
        config.paths.tests_dir if not os.path.isabs(config.paths.tests_dir) else config.paths.tests_dir,
    ]
    
    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)

# Initialize config on module load
if __name__ == "__main__":
    # Test configuration loading
    cfg = get_config()
    print(f"Learning Rate: {cfg.hyperparameters.learning_rate}")
    print(f"Batch Size: {cfg.hyperparameters.batch_size}")
    print(f"Seed: {cfg.hyperparameters.seed}")
    print(f"RAM Limit: {cfg.safety.ram_limit_gb} GB")
    print(f"Max Param Increase: {cfg.safety.max_param_increase_percent}%")
    
    # Ensure directories exist
    ensure_directories()
    print("Directories ensured.")
    
    # Verify default values match spec
    assert cfg.hyperparameters.learning_rate == 5e-5, "Learning rate mismatch"
    assert cfg.hyperparameters.batch_size == 4, "Batch size mismatch"
    assert cfg.hyperparameters.seed == 42, "Seed mismatch"
    assert cfg.safety.max_param_increase_percent == 30.0, "Param increase constraint mismatch"
    print("All default values verified.")
