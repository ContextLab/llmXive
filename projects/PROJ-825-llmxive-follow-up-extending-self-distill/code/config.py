"""
Configuration management for the project.

Implements T006 requirements.
"""
import os
import argparse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class SeedConfig:
    seed: int = 42

@dataclass
class ModelConfig:
    # Gating parameters
    gating_alpha: float = 1.0
    gating_beta: float = 1.0
    gating_threshold: float = 0.5
    # Model paths
    student_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"
    teacher_model_name: str = "Qwen/Qwen2.5-7B-Instruct"
    # Quantization
    use_8bit: bool = True

@dataclass
class TrainingConfig:
    max_steps: int = 1000
    batch_size: int = 1
    learning_rate: float = 1e-5
    variant: str = "student-only" # Options: student-only, baseline, grpo
    model: ModelConfig = field(default_factory=ModelConfig)

@dataclass
class EnvironmentConfig:
    env_name: str = "alfworld"
    task_type: str = "pick_and_place"

@dataclass
class LoggingConfig:
    log_dir: str = "data/processed"
    save_interval: int = 100

@dataclass
class StatisticalConfig:
    n_runs: int = 5
    significance_level: float = 0.05

@dataclass
class ProjectConfig:
    name: str = "llmXive-follow-up"
    version: str = "0.1.0"

@dataclass
class FullConfig:
    seed: SeedConfig = field(default_factory=SeedConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    statistical: StatisticalConfig = field(default_factory=StatisticalConfig)
    project: ProjectConfig = field(default_factory=ProjectConfig)

def get_config() -> FullConfig:
    """Get the full configuration."""
    return FullConfig()

def parse_args_to_dict() -> Dict[str, Any]:
    """Parse command line arguments into a dictionary."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", type=str, default="student-only")
    parser.add_argument("--env", type=str, default="alfworld")
    args = parser.parse_args()
    return vars(args)
