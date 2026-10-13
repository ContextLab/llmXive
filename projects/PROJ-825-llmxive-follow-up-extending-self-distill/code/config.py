"""
Configuration management for the project.

Implements T006 requirements: defines SEEDS list, DEFAULTS dict,
and provides dataclass-based configurations along with argument parsing.
"""
import os
import argparse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ----------------------------------------------------------------------
# Public constants required by the verification step
# ----------------------------------------------------------------------
# List of seeds to be used for reproducible runs (5 seeds as specified)
SEEDS: List[int] = [0, 1, 2, 3, 4]

# Default hyperparameter values matching the plan specifications.
# These are kept in a simple dictionary for easy access from scripts
# that expect a flat config mapping.
DEFAULTS: Dict[str, Any] = {
    # General experiment settings
    "seed": 42,
    "variant": "student-only",   # Options: student-only, baseline, grpo, student-only-replay
    "env": "alfworld",
    # Training hyperparameters
    "max_steps": 1000,
    "batch_size": 1,
    "learning_rate": 1e-5,
    # Gating hyperparameters
    "gating_alpha": 1.0,
    "gating_beta": 1.0,
    "gating_threshold": 0.5,
    # Model identifiers
    "student_model_name": "Qwen/Qwen2.5-1.5B-Instruct",
    "teacher_model_name": "Qwen/Qwen2.5-7B-Instruct",
    # Quantization flag
    "use_8bit": True,
}

# ----------------------------------------------------------------------
# Dataclass based configuration structures (kept for richer type usage)
# ----------------------------------------------------------------------
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
    variant: str = "student-only"  # Options: student-only, baseline, grpo, student-only-replay
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
    """
    Parse command‑line arguments into a dictionary.
    The parser mirrors the arguments used in the quickstart
    documentation, providing defaults that align with ``DEFAULTS``.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", type=str, default=DEFAULTS["variant"],
                        help="Experiment variant (student-only, baseline, grpo, student-only-replay).")
    parser.add_argument("--env", type=str, default=DEFAULTS["env"],
                        help="Environment name (alfworld or webshop).")
    parser.add_argument("--seed", type=int, default=DEFAULTS["seed"],
                        help="Random seed for reproducibility.")
    parser.add_argument("--max-steps", type=int, default=DEFAULTS["max_steps"],
                        help="Maximum number of training steps.")
    parser.add_argument("--output-dir", type=str, default="data/processed",
                        help="Directory where run artifacts will be stored.")
    # Additional optional hyper‑parameters can be supplied via the CLI;
    # they are captured generically so downstream code can read them.
    parser.add_argument("--learning-rate", type=float, default=DEFAULTS["learning_rate"],
                        help="Learning rate for the optimizer.")
    parser.add_argument("--batch-size", type=int, default=DEFAULTS["batch_size"],
                        help="Batch size per training step.")
    parser.add_argument("--gating-alpha", type=float, default=DEFAULTS["gating_alpha"],
                        help="Weight for token entropy in gating score.")
    parser.add_argument("--gating-beta", type=float, default=DEFAULTS["gating_beta"],
                        help="Weight for context stability in gating score.")
    parser.add_argument("--gating-threshold", type=float, default=DEFAULTS["gating_threshold"],
                        help="Threshold for applying the gate.")
    parser.add_argument("--student-model-name", type=str, default=DEFAULTS["student_model_name"],
                        help="HuggingFace identifier for the student model.")
    parser.add_argument("--teacher-model-name", type=str, default=DEFAULTS["teacher_model_name"],
                        help="HuggingFace identifier for the teacher model.")
    parser.add_argument("--use-8bit", action="store_true",
                        help="Enable 8‑bit quantization for model loading.")
    args = parser.parse_args()
    # Convert argparse.Namespace to a plain dict for downstream convenience.
    return vars(args)