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
    """Configuration for models."""
    teacher_model_name: str = "Qwen/Qwen2.5-1.7B"
    student_model_name: str = "Qwen/Qwen2.5-1.7B"
    sentence_transformer_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    quantization_bits: int = 8
    max_context_length: int = 2048


@dataclass
class TrainingConfig:
    """Configuration for training runs."""
    max_episodes: int = 100
    max_steps_per_episode: int = 50
    early_stop_reward_threshold: float = 0.8
    early_stop_consecutive_episodes: int = 3
    learning_rate: float = 1e-4
    batch_size: int = 1
    variant: str = "student-only"  # Options: student-only, baseline, grpo


@dataclass
class EnvironmentConfig:
    """Configuration for environments."""
    alfworld_env: str = "alfworld"
    webshop_env: str = "webshop"
    random_seed: int = 42


@dataclass
class LoggingConfig:
    """Configuration for logging outputs."""
    output_dir: str = "data/processed"
    training_log_jsonl: str = "training_run_logs.jsonl"
    training_log_csv: str = "training_run_logs.csv"
    gating_signal_log_jsonl: str = "gating_signal_logs.jsonl"
    gating_signal_log_csv: str = "gating_signal_logs.csv"


@dataclass
class StatisticalConfig:
    """Configuration for statistical analysis."""
    bootstrap_iterations: int = 1000
    confidence_level: float = 0.95
    significance_threshold: float = 0.05


@dataclass
class ProjectConfig:
    """Top-level project configuration."""
    project_name: str = "llmXive-follow-up-extending-self-distill"
    version: str = "0.1.0"
    seed: SeedConfig = field(default_factory=SeedConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    environment: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    statistical: StatisticalConfig = field(default_factory=StatisticalConfig)


def get_config() -> ProjectConfig:
    """Get the project configuration."""
    return ProjectConfig()


def parse_args_to_dict() -> Dict[str, Any]:
    """Parse command line arguments and return as a dictionary."""
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--variant", type=str, default="student-only",
                        choices=["student-only", "baseline", "grpo"],
                        help="Training variant")
    parser.add_argument("--max-episodes", type=int, default=100, help="Max episodes")
    parser.add_argument("--output-dir", type=str, default="data/processed",
                        help="Output directory for logs")

    args = parser.parse_args()
    return vars(args)