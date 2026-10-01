import os
import argparse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class SeedConfig:
    """Configuration for random seeds."""
    seed: int = 42
    torch_seed: int = 42
    numpy_seed: int = 42

@dataclass
class ModelConfig:
    """Configuration for model loading and parameters."""
    teacher_model_name: str = "Qwen/Qwen2.5-1.7B"
    student_model_name: str = "Qwen/Qwen2.5-1.7B"
    quantization_bits: int = 8
    device: str = "cpu"
    context_window: int = 2048
    max_new_tokens: int = 256

@dataclass
class TrainingConfig:
    """Configuration for training hyperparameters."""
    variant: str = "student-only" # Options: student-only, baseline, grpo
    max_steps: int = 1000
    batch_size: int = 1
    learning_rate: float = 1e-5
    reward_threshold: float = 0.8
    consecutive_wins: int = 3
    early_stopping_patience: int = 5

@dataclass
class EnvironmentConfig:
    """Configuration for environment settings."""
    env_type: str = "alfworld" # Options: alfworld, webshop
    task_subset: Optional[str] = None
    max_episode_steps: int = 50

@dataclass
class LoggingConfig:
    """Configuration for logging and output paths."""
    output_dir: str = "data/processed"
    log_level: str = "INFO"
    log_metrics: bool = True
    log_trajectories: bool = True
    save_interval: int = 100

@dataclass
class StatisticalConfig:
    """Configuration for statistical analysis."""
    n_bootstrap: int = 1000
    confidence_level: float = 0.95
    significance_level: float = 0.05

@dataclass
class ProjectConfig:
    """General project configuration."""
    project_name: str = "llmxive-follow-up-extending-self-distill"
    version: str = "0.1.0"
    debug: bool = False

@dataclass
class FullConfig:
    """Aggregated configuration."""
    seed: SeedConfig = field(default_factory=SeedConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    statistical: StatisticalConfig = field(default_factory=StatisticalConfig)
    project: ProjectConfig = field(default_factory=ProjectConfig)

def get_config(args: Optional[argparse.Namespace] = None) -> FullConfig:
    """
    Constructs a FullConfig object.
    If args is provided, it overrides defaults from command line.
    """
    config = FullConfig()
    
    if args:
        if hasattr(args, 'seed'):
            config.seed.seed = args.seed
        if hasattr(args, 'variant'):
            config.training.variant = args.variant
        if hasattr(args, 'env_type'):
            config.environment.env_type = args.env_type
        if hasattr(args, 'output_dir'):
            config.logging.output_dir = args.output_dir
    
    return config

def parse_args_to_dict() -> Dict[str, Any]:
    """
    Parses command line arguments and returns a dictionary.
    Used for dynamic configuration updates.
    """
    parser = argparse.ArgumentParser(description="LLM-Xive Research Pipeline")
    
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--variant', type=str, default='student-only', 
                        choices=['student-only', 'baseline', 'grpo'],
                        help='Agent variant to run')
    parser.add_argument('--env_type', type=str, default='alfworld',
                        choices=['alfworld', 'webshop'],
                        help='Environment to run against')
    parser.add_argument('--output_dir', type=str, default='data/processed',
                        help='Directory for output logs and artifacts')
    
    return vars(parser.parse_args())
