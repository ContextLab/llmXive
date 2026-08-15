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

@dataclass
class Hyperparameters:
    """Training hyperparameters."""
    learning_rate: float = 5e-5
    batch_size: int = 4
    seed: int = 42
    gradient_accumulation_steps: int = 4
    max_epochs: int = 1
    weight_decay: float = 0.01
    warmup_steps: int = 0
    max_grad_norm: float = 1.0
    num_resamples: int = 1000  # For bootstrap testing

@dataclass
class SafetyConstraints:
    """Safety and resource constraints."""
    max_param_increase_percent: float = 0.30  # 30% limit per FR-019
    max_ram_gb: float = 7.0
    max_cycle_time_seconds: float = 3600.0  # 1 hour per cycle
    max_total_time_hours: float = 12.0
    max_attempts: int = 3
    degradation_threshold_percent: float = 0.05  # 5% degradation triggers early stop

@dataclass
class PathConfig:
    """Path definitions for project artifacts."""
    # Root paths
    project_root: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Data directories
    data_raw: str = field(init=False)
    data_processed: str = field(init=False)
    
    # Results directories
    results_dir: str = field(init=False)
    results_logs: str = field(init=False)
    results_checkpoints: str = field(init=False)
    
    # Code directories
    code_dir: str = field(init=False)
    tests_dir: str = field(init=False)
    specs_dir: str = field(init=False)
    
    # State directory
    state_dir: str = field(init=False)
    
    # Specific file paths
    trajectory_file: str = field(init=False)
    trade_off_file: str = field(init=False)
    final_report_file: str = field(init=False)
    state_file: str = field(init=False)
    
    def __post_init__(self):
        """Initialize derived paths."""
        self.data_raw = os.path.join(self.project_root, "data", "raw")
        self.data_processed = os.path.join(self.project_root, "data", "processed")
        self.results_dir = os.path.join(self.project_root, "results")
        self.results_logs = os.path.join(self.results_dir, "logs")
        self.results_checkpoints = os.path.join(self.results_dir, "checkpoints")
        self.code_dir = os.path.join(self.project_root, "code")
        self.tests_dir = os.path.join(self.project_root, "tests")
        self.specs_dir = os.path.join(self.project_root, "specs")
        self.state_dir = os.path.join(self.project_root, "state")
        self.trajectory_file = os.path.join(self.results_dir, "trajectory.json")
        self.trade_off_file = os.path.join(self.results_dir, "trade_off_analysis.json")
        self.final_report_file = os.path.join(self.results_dir, "final_report.md")
        self.state_file = os.path.join(self.state_dir, "state.json")

@dataclass
class Config:
    """Master configuration class."""
    hyperparameters: Hyperparameters = field(default_factory=Hyperparameters)
    safety: SafetyConstraints = field(default_factory=SafetyConstraints)
    paths: PathConfig = field(default_factory=PathConfig)
    
    def set_seed(self):
        """Set random seeds for reproducibility."""
        random.seed(self.hyperparameters.seed)
        np.random.seed(self.hyperparameters.seed)
        torch.manual_seed(self.hyperparameters.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.hyperparameters.seed)

# Global config instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
        _config.set_seed()
    return _config

def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    config = get_config()
    dirs = [
        config.paths.data_raw,
        config.paths.data_processed,
        config.paths.results_dir,
        config.paths.results_logs,
        config.paths.results_checkpoints,
        config.paths.state_dir,
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def get_trajectory_path() -> str:
    """Get the path to the trajectory file."""
    return get_config().paths.trajectory_file

def get_log_path(cycle_number: int) -> str:
    """Get the path to a cycle log file."""
    return os.path.join(get_config().paths.results_logs, f"cycle_{cycle_number}.log")

def get_checkpoint_path(cycle_number: int) -> str:
    """Get the path to a checkpoint file."""
    return os.path.join(get_config().paths.results_checkpoints, f"cycle_{cycle_number}.pt")

# Verification helpers
def verify_default_values() -> bool:
    """Verify that default configuration values match the specification."""
    config = get_config()
    assert config.hyperparameters.learning_rate == 5e-5, "Learning rate must be 5e-5"
    assert config.hyperparameters.batch_size == 4, "Batch size must be 4"
    assert config.hyperparameters.seed == 42, "Seed must be 42"
    assert config.safety.max_param_increase_percent == 0.30, "Max param increase must be 30%"
    assert config.safety.max_ram_gb == 7.0, "Max RAM must be 7.0 GB"
    assert config.safety.degradation_threshold_percent == 0.05, "Degradation threshold must be 5%"
    return True

if __name__ == "__main__":
    # Run verification when executed directly
    config = get_config()
    print("Configuration loaded successfully:")
    print(f"  Learning rate: {config.hyperparameters.learning_rate}")
    print(f"  Batch size: {config.hyperparameters.batch_size}")
    print(f"  Seed: {config.hyperparameters.seed}")
    print(f"  Max param increase: {config.safety.max_param_increase_percent * 100}%")
    print(f"  Max RAM: {config.safety.max_ram_gb} GB")
    print(f"  Degradation threshold: {config.safety.degradation_threshold_percent * 100}%")
    print(f"  Trajectory file: {config.paths.trajectory_file}")
    
    if verify_default_values():
        print("\nAll default values verified successfully.")
    else:
        print("\nWARNING: Some default values do not match specification!")
        exit(1)
