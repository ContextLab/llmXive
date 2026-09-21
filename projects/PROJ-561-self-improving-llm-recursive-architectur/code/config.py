import os
import random
import numpy as np
import torch
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Hyperparameters:
    learning_rate: float = 5e-5
    batch_size: int = 4
    seed: int = 42
    num_epochs: int = 1
    max_param_increase_percent: float = 30.0
    bootstrap_resamples: int = 1000
    max_cycles: int = 3
    retry_limit: int = 2
    timeout_seconds: int = 300

@dataclass
class SafetyConstraints:
    param_limit: float = 0.30
    ram_limit_gb: float = 7.0
    max_attempts: int = 3
    distinctness_threshold: float = 0.05

@dataclass
class PathConfig:
    root: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    code_dir: str = field(default="code")
    data_raw_dir: str = field(default="data/raw")
    data_processed_dir: str = field(default="data/processed")
    results_dir: str = field(default="results")
    specs_dir: str = field(default="specs")
    tests_dir: str = field(default="tests")
    state_dir: str = field(default="state")
    figures_dir: str = field(default="figures")
    trajectory_file: str = field(default="results/trajectory.json")
    log_file: str = field(default="results/cycle_logs.jsonl")
    final_report_file: str = field(default="results/final_report.md")

@dataclass
class Config:
    hyperparameters: Hyperparameters = field(default_factory=Hyperparameters)
    safety: SafetyConstraints = field(default_factory=SafetyConstraints)
    paths: PathConfig = field(default_factory=PathConfig)

_global_config: Optional[Config] = None

def get_config() -> Config:
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def set_config(cfg: Config) -> None:
    global _global_config
    _global_config = cfg

def get_learning_rate() -> float:
    return get_config().hyperparameters.learning_rate

def get_batch_size() -> int:
    return get_config().hyperparameters.batch_size

def get_seed() -> int:
    return get_config().hyperparameters.seed

def get_ram_limit() -> float:
    return get_config().safety.ram_limit_gb

def get_trajectory_path() -> str:
    return os.path.join(get_config().paths.root, get_config().paths.trajectory_file)

def get_max_param_increase_percent() -> float:
    return get_config().safety.param_limit * 100.0

def get_bootstrap_resamples() -> int:
    return get_config().hyperparameters.bootstrap_resamples

def set_seed(seed: Optional[int] = None) -> None:
    if seed is None:
        seed = get_seed()
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def ensure_directories() -> None:
    cfg = get_config()
    dirs = [
        os.path.join(cfg.paths.root, cfg.paths.data_raw_dir),
        os.path.join(cfg.paths.root, cfg.paths.data_processed_dir),
        os.path.join(cfg.paths.root, cfg.paths.results_dir),
        os.path.join(cfg.paths.root, cfg.paths.specs_dir),
        os.path.join(cfg.paths.root, cfg.paths.tests_dir),
        os.path.join(cfg.paths.root, cfg.paths.tests_dir, "unit"),
        os.path.join(cfg.paths.root, cfg.paths.tests_dir, "integration"),
        os.path.join(cfg.paths.root, cfg.paths.state_dir),
        os.path.join(cfg.paths.root, cfg.paths.figures_dir),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

if __name__ == "__main__":
    cfg = get_config()
    print(f"Learning Rate: {cfg.hyperparameters.learning_rate}")
    print(f"Batch Size: {cfg.hyperparameters.batch_size}")
    print(f"Seed: {cfg.hyperparameters.seed}")
    print(f"Param Limit: {cfg.safety.param_limit}")
    print(f"RAM Limit: {cfg.safety.ram_limit_gb} GB")
    print(f"Trajectory Path: {get_trajectory_path()}")
    ensure_directories()
    print("Directories ensured.")
