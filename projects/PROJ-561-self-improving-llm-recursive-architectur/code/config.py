"""
Configuration management for the self-improving LLM pipeline.
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
    # Learning rate
    learning_rate: float = 5e-5
    
    # Batch size (FIXED at 4 per FR-004, no auto-scaling)
    batch_size: int = 4
    
    # Random seed for reproducibility
    seed: int = 42
    
    # Number of epochs per cycle
    epochs_per_cycle: int = 1
    
    # Weight decay for AdamW
    weight_decay: float = 0.01
    
    # Gradient clipping norm
    gradient_clip_norm: float = 1.0
    
    # Max sequence length
    max_seq_length: int = 512
    
    # Warmup steps (fraction of total steps)
    warmup_fraction: float = 0.1
    
    def set_seed(self):
        """Set all random seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)


@dataclass
class SafetyConstraints:
    """Safety and resource constraints for the pipeline."""
    # Maximum parameter increase allowed (30% as per spec)
    max_param_increase_ratio: float = 1.3
    
    # Maximum RAM usage in GB (7GB per T004)
    max_ram_gb: float = 7.0
    
    # Maximum training time per cycle in seconds (1.5 hours for US-1)
    max_cycle_time_seconds: int = 5400
    
    # Maximum total runtime in seconds (6 hours for full run)
    max_total_runtime_seconds: int = 21600
    
    # Early stop threshold: degradation >= 5% triggers early stop
    early_stop_degradation_threshold: float = 0.05
    
    # Maximum number of retry attempts for failed cycles
    max_retry_attempts: int = 2
    
    # Timeout for individual benchmark evaluations (seconds)
    benchmark_timeout_seconds: int = 300
    
    # Minimum improvement required to accept a modification (for self-acceptance)
    min_acceptable_improvement: float = 0.0
    
    def validate_param_count(self, current_count: int, proposed_count: int) -> bool:
        """Check if proposed parameter count is within safety limits."""
        ratio = proposed_count / current_count if current_count > 0 else float('inf')
        return ratio <= self.max_param_increase_ratio


@dataclass
class PathConfig:
    """Path configuration for project directories and files."""
    # Base project root (assumes code/ is at project root)
    project_root: str = field(default_factory=lambda: os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Data directories
    data_raw_dir: str = field(default="data/raw")
    data_processed_dir: str = field(default="data/processed")
    data_cache_dir: str = field(default="data/cache")
    
    # Results directory
    results_dir: str = field(default="results")
    
    # Specs directory
    specs_dir: str = field(default="specs")
    
    # Code directory
    code_dir: str = field(default="code")
    
    # Tests directory
    tests_dir: str = field(default="tests")
    
    # Logs directory
    logs_dir: str = field(default="logs")
    
    # Checkpoints directory
    checkpoints_dir: str = field(default="checkpoints")
    
    # Prompts directory
    prompts_dir: str = field(default="prompts")
    
    # Schemas directory
    schemas_dir: str = field(default="schemas")
    
    # Specific file paths
    trajectory_file: str = field(default="results/trajectory.json")
    trade_off_file: str = field(default="results/trade_off_analysis.json")
    modification_proposal_prompt: str = field(default="prompts/modification_proposal.txt")
    config_file: str = field(default="config.yaml")
    
    def __post_init__(self):
        """Ensure all directories exist."""
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create all required directories if they don't exist."""
        dirs = [
            self.data_raw_dir,
            self.data_processed_dir,
            self.data_cache_dir,
            self.results_dir,
            self.specs_dir,
            self.code_dir,
            self.tests_dir,
            self.logs_dir,
            self.checkpoints_dir,
            self.prompts_dir,
            self.schemas_dir
        ]
        
        for dir_path in dirs:
            full_path = os.path.join(self.project_root, dir_path)
            os.makedirs(full_path, exist_ok=True)
    
    def get_full_path(self, relative_path: str) -> str:
        """Get full absolute path for a relative path."""
        return os.path.join(self.project_root, relative_path)
    
    def get_trajectory_path(self) -> str:
        """Get full path to trajectory file."""
        return self.get_full_path(self.trajectory_file)
    
    def get_trade_off_path(self) -> str:
        """Get full path to trade-off analysis file."""
        return self.get_full_path(self.trade_off_file)


@dataclass
class Config:
    """Main configuration class combining all settings."""
    hyperparameters: Hyperparameters = field(default_factory=Hyperparameters)
    safety: SafetyConstraints = field(default_factory=SafetyConstraints)
    paths: PathConfig = field(default_factory=PathConfig)
    
    def __post_init__(self):
        """Initialize seeds and validate configuration."""
        self.hyperparameters.set_seed()
    
    def summary(self) -> dict:
        """Return a dictionary summary of the configuration."""
        return {
            'hyperparameters': {
                'learning_rate': self.hyperparameters.learning_rate,
                'batch_size': self.hyperparameters.batch_size,
                'seed': self.hyperparameters.seed,
                'epochs_per_cycle': self.hyperparameters.epochs_per_cycle,
                'weight_decay': self.hyperparameters.weight_decay,
                'gradient_clip_norm': self.hyperparameters.gradient_clip_norm,
                'max_seq_length': self.hyperparameters.max_seq_length,
                'warmup_fraction': self.hyperparameters.warmup_fraction
            },
            'safety': {
                'max_param_increase_ratio': self.safety.max_param_increase_ratio,
                'max_ram_gb': self.safety.max_ram_gb,
                'max_cycle_time_seconds': self.safety.max_cycle_time_seconds,
                'max_total_runtime_seconds': self.safety.max_total_runtime_seconds,
                'early_stop_degradation_threshold': self.safety.early_stop_degradation_threshold,
                'max_retry_attempts': self.safety.max_retry_attempts,
                'benchmark_timeout_seconds': self.safety.benchmark_timeout_seconds,
                'min_acceptable_improvement': self.safety.min_acceptable_improvement
            },
            'paths': {
                'project_root': self.paths.project_root,
                'data_raw_dir': self.paths.data_raw_dir,
                'data_processed_dir': self.paths.data_processed_dir,
                'results_dir': self.paths.results_dir,
                'trajectory_file': self.paths.trajectory_file
            }
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