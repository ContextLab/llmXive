"""
Configuration module for the self-improving LLM recursive architecture project.
Defines hyperparameters, safety constraints, and path configurations.
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional
import random
import numpy as np
import torch

# --- Hyperparameters ---
@dataclass
class Hyperparameters:
    """Training and optimization hyperparameters."""
    learning_rate: float = 5e-5
    batch_size: int = 4
    seed: int = 42
    gradient_accumulation_steps: int = 4
    max_epochs: int = 1  # Single epoch per cycle as per MVP
    warmup_steps: int = 0
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0

    def set_seed(self):
        """Set random seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)

# --- Safety Constraints ---
@dataclass
class SafetyConstraints:
    """Safety and resource constraints for the recursive loop."""
    # Maximum allowed parameter increase (30% of baseline)
    max_param_increase_ratio: float = 0.30
    # RAM limit in GB (hard watchdog)
    ram_limit_gb: float = 7.0
    # Maximum training time per cycle in seconds (2 hours)
    max_cycle_time_seconds: int = 7200
    # Maximum total pipeline time in seconds (6 hours)
    max_total_time_seconds: int = 21600
    # Early stop threshold: degradation >= 5% from baseline
    early_stop_degradation_threshold: float = 0.05
    # Minimum batch size before OOM termination
    min_batch_size: int = 1

# --- Path Configuration ---
@dataclass
class PathConfig:
    """File system paths for project artifacts."""
    # Root directory (assumed to be the project root where code/ resides)
    root_dir: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Data directories
    data_raw: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'raw'))
    data_processed: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'processed'))
    data_checkpoints: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'checkpoints'))
    
    # Results directories
    results_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results'))
    results_logs: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'logs'))
    figures_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'figures'))
    
    # Specific output files
    trajectory_file: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'trajectory.json'))
    trade_off_file: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'trade_off_analysis.json'))
    
    # Code directories
    code_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__))))
    specs_dir: str = field(default_factory=lambda: os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'specs'))
    
    def __post_init__(self):
        """Ensure directories exist."""
        dirs = [
            self.data_raw, self.data_processed, self.data_checkpoints,
            self.results_dir, self.results_logs, self.figures_dir
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

# --- Global Configuration ---
_config_instance: Optional[tuple] = None

def get_config() -> tuple:
    """
    Returns a tuple of (Hyperparameters, SafetyConstraints, PathConfig).
    Initializes them if not already done.
    """
    global _config_instance
    if _config_instance is None:
        hp = Hyperparameters()
        sc = SafetyConstraints()
        pc = PathConfig()
        hp.set_seed()
        _config_instance = (hp, sc, pc)
    return _config_instance

def set_config(learning_rate: float = None, batch_size: int = None, seed: int = None, ram_limit: float = None):
    """
    Updates the global configuration with new values.
    Resets the instance so get_config() picks up changes.
    """
    global _config_instance
    if _config_instance is not None:
        hp, sc, pc = _config_instance
        if learning_rate is not None:
            hp.learning_rate = learning_rate
        if batch_size is not None:
            hp.batch_size = batch_size
        if seed is not None:
            hp.seed = seed
            hp.set_seed()
        if ram_limit is not None:
            sc.ram_limit_gb = ram_limit
        _config_instance = (hp, sc, pc)

def get_config_summary() -> str:
    """
    Returns a human-readable summary of the current configuration.
    """
    hp, sc, pc = get_config()
    summary = [
        "=== Configuration Summary ===",
        f"Learning Rate: {hp.learning_rate}",
        f"Batch Size: {hp.batch_size}",
        f"Seed: {hp.seed}",
        f"Max Param Increase: {sc.max_param_increase_ratio * 100:.1f}%",
        f"RAM Limit: {sc.ram_limit_gb} GB",
        f"Max Cycle Time: {sc.max_cycle_time_seconds} s",
        f"Trajectory File: {pc.trajectory_file}",
        "============================="
    ]
    return "\n".join(summary)

# Convenience accessors for common fields
def get_learning_rate() -> float:
    return get_config()[0].learning_rate

def get_batch_size() -> int:
    return get_config()[0].batch_size

def get_seed() -> int:
    return get_config()[0].seed

def get_ram_limit() -> float:
    return get_config()[1].ram_limit_gb

def get_trajectory_path() -> str:
    return get_config()[2].trajectory_file