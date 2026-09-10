"""
Environment configuration management for random seeds and model paths.

This module defines the central configuration for the Socratic Transformers project,
including model IDs, data paths, and random seed management for reproducibility.
"""
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
STATE_ROOT = PROJECT_ROOT / "state"
RESULTS_ROOT = PROJECT_ROOT / "results"

# Model Configuration
# Base model for generation and fine-tuning (small, CPU-friendly)
BASE_MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Critic model for adversarial feedback (frozen, small)
# Using a small model to fit within CPU constraints while providing critique
CRITIC_MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

# Path to the question bank (GSM8K/MATH processed data)
QUESTION_BANK_PATH = str(DATA_ROOT / "processed" / "static_tuples.jsonl")

# Random Seed Configuration
DEFAULT_SEED = 42


@dataclass
class SocraticConfig:
    """
    Central configuration dataclass for the Socratic Transformers project.
    """
    # Model IDs
    base_model_id: str = BASE_MODEL_ID
    critic_model_id: str = CRITIC_MODEL_ID

    # Paths
    project_root: Path = field(default_factory=lambda: PROJECT_ROOT)
    data_root: Path = field(default_factory=lambda: DATA_ROOT)
    state_root: Path = field(default_factory=lambda: STATE_ROOT)
    results_root: Path = field(default_factory=lambda: RESULTS_ROOT)
    question_bank_path: str = field(default_factory=lambda: QUESTION_BANK_PATH)

    # Training/Generation Parameters
    seed: int = DEFAULT_SEED
    max_length: int = 512
    batch_size: int = 1
    gradient_accumulation_steps: int = 4

    # Quantization
    use_4bit: bool = True

    # Logging
    log_level: str = "INFO"

    def __post_init__(self):
        """Ensure paths are Path objects."""
        if isinstance(self.project_root, str):
            self.project_root = Path(self.project_root)
        if isinstance(self.data_root, str):
            self.data_root = Path(self.data_root)
        if isinstance(self.state_root, str):
            self.state_root = Path(self.state_root)
        if isinstance(self.results_root, str):
            self.results_root = Path(self.results_root)


# Global configuration instance
_global_config: Optional[SocraticConfig] = None


def get_config() -> SocraticConfig:
    """
    Get the global configuration instance.
    Creates one if it doesn't exist.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
    return _global_config


def set_global_config(config: SocraticConfig) -> None:
    """
    Set the global configuration instance.
    """
    global _global_config
    _global_config = config


def load_config_from_env() -> SocraticConfig:
    """
    Load configuration from environment variables, falling back to defaults.
    """
    base_model = os.getenv("BASE_MODEL_ID", BASE_MODEL_ID)
    critic_model = os.getenv("CRITIC_MODEL_ID", CRITIC_MODEL_ID)
    seed = int(os.getenv("RANDOM_SEED", DEFAULT_SEED))
    question_bank = os.getenv("QUESTION_BANK_PATH", QUESTION_BANK_PATH)

    return SocraticConfig(
        base_model_id=base_model,
        critic_model_id=critic_model,
        seed=seed,
        question_bank_path=question_bank
    )


def set_seed(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility across Python, NumPy, and PyTorch (if available).
    """
    if seed is None:
        seed = get_config().seed

    random.seed(seed)
    np.random.seed(seed)

    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def init_project() -> None:
    """
    Initialize project directories based on configuration.
    """
    config = get_config()
    dirs = [
        config.data_root / "raw",
        config.data_root / "processed",
        config.data_root / "results",
        config.state_root,
        config.results_root
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """
    Main entry point for testing configuration.
    """
    config = get_config()
    print(f"Project Root: {config.project_root}")
    print(f"Base Model ID: {config.base_model_id}")
    print(f"Critic Model ID: {config.critic_model_id}")
    print(f"Question Bank Path: {config.question_bank_path}")
    print(f"Seed: {config.seed}")


if __name__ == "__main__":
    main()