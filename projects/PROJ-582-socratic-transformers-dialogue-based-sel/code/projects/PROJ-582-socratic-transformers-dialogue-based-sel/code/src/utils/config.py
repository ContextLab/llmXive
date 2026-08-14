"""
Environment configuration management for the Socratic Transformers project.

This module handles random seeds, model paths, and critical hyperparameters
required for reproducibility and consistent execution across the pipeline.
"""

import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np

# Project Root relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class SocraticConfig:
    """
    Central configuration container for the Socratic Transformers pipeline.

    Attributes:
        CRITIC_MODEL_ID: HuggingFace model ID for the frozen critic model.
        BASE_MODEL_ID: HuggingFace model ID for the base model to be fine-tuned.
        QUESTION_BANK_PATH: Path to the question bank or dataset source.
        SEED: Random seed for reproducibility.
        MAX_SEQ_LENGTH: Maximum sequence length for tokenization.
        OUTPUT_DIR: Root directory for all generated artifacts.
        DATA_RAW_DIR: Directory for raw downloaded datasets.
        DATA_PROCESSED_DIR: Directory for processed dataset files.
        DATA_RESULTS_DIR: Directory for evaluation results and checkpoints.
        STATE_DIR: Directory for manifests and state tracking.
    """

    # Model Identifiers (Required)
    CRITIC_MODEL_ID: str = "distilbert-base-uncased"
    BASE_MODEL_ID: str = "distilbert-base-uncased"

    # Data Paths
    QUESTION_BANK_PATH: str = field(default_factory=lambda: str(_PROJECT_ROOT / "data" / "raw"))

    # Randomness
    SEED: int = 42

    # Hyperparameters
    MAX_SEQ_LENGTH: int = 512
    BATCH_SIZE: int = 2
    GRADIENT_ACCUMULATION_STEPS: int = 4

    # Directory Structure (Relative to project root)
    OUTPUT_DIR: str = field(default_factory=lambda: str(_PROJECT_ROOT / "data" / "results"))
    DATA_RAW_DIR: str = field(default_factory=lambda: str(_PROJECT_ROOT / "data" / "raw"))
    DATA_PROCESSED_DIR: str = field(default_factory=lambda: str(_PROJECT_ROOT / "data" / "processed"))
    DATA_RESULTS_DIR: str = field(default_factory=lambda: str(_PROJECT_ROOT / "data" / "results"))
    STATE_DIR: str = field(default_factory=lambda: str(_PROJECT_ROOT / "state"))

    # Training Constraints
    CPU_TIMEOUT_HOURS: int = 5
    MAX_MEMORY_GB: float = 6.5

    def __post_init__(self):
        """Ensure paths are Path objects if strings are provided."""
        self.QUESTION_BANK_PATH = Path(self.QUESTION_BANK_PATH)
        self.OUTPUT_DIR = Path(self.OUTPUT_DIR)
        self.DATA_RAW_DIR = Path(self.DATA_RAW_DIR)
        self.DATA_PROCESSED_DIR = Path(self.DATA_PROCESSED_DIR)
        self.DATA_RESULTS_DIR = Path(self.DATA_RESULTS_DIR)
        self.STATE_DIR = Path(self.STATE_DIR)


# Global configuration instance
_global_config: Optional[SocraticConfig] = None


def get_config() -> SocraticConfig:
    """
    Returns the global SocraticConfig instance.
    If not initialized, creates a default one.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
    return _global_config


def set_global_config(config: SocraticConfig) -> None:
    """
    Sets the global configuration instance explicitly.
    Useful for testing or overriding defaults.
    """
    global _global_config
    _global_config = config


def load_config_from_env() -> SocraticConfig:
    """
    Loads configuration from environment variables, falling back to defaults.

    Environment Variables:
        CRITIC_MODEL_ID: Overrides the critic model ID.
        BASE_MODEL_ID: Overrides the base model ID.
        QUESTION_BANK_PATH: Overrides the question bank path.
        SEED: Overrides the random seed.
        MAX_SEQ_LENGTH: Overrides max sequence length.
    """
    config = SocraticConfig()

    # Override with environment variables if present
    if os.getenv("CRITIC_MODEL_ID"):
        config.CRITIC_MODEL_ID = os.getenv("CRITIC_MODEL_ID")
    if os.getenv("BASE_MODEL_ID"):
        config.BASE_MODEL_ID = os.getenv("BASE_MODEL_ID")
    if os.getenv("QUESTION_BANK_PATH"):
        config.QUESTION_BANK_PATH = Path(os.getenv("QUESTION_BANK_PATH"))
    if os.getenv("SEED"):
        try:
            config.SEED = int(os.getenv("SEED"))
        except ValueError:
            pass
    if os.getenv("MAX_SEQ_LENGTH"):
        try:
            config.MAX_SEQ_LENGTH = int(os.getenv("MAX_SEQ_LENGTH"))
        except ValueError:
            pass

    return config


def set_seed(seed: Optional[int] = None) -> None:
    """
    Sets the random seed for Python, NumPy, and PyTorch (if available).

    Args:
        seed: The seed value. If None, uses the seed from the global config.
    """
    if seed is None:
        seed = get_config().SEED

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
    Initializes the project directory structure based on the configuration.
    Creates necessary folders for data, results, and state if they don't exist.
    """
    config = get_config()
    directories = [
        config.DATA_RAW_DIR,
        config.DATA_PROCESSED_DIR,
        config.DATA_RESULTS_DIR,
        config.STATE_DIR,
        config.OUTPUT_DIR,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """
    CLI entry point to print current configuration.
    """
    config = get_config()
    print("Socratic Transformers Configuration:")
    print(f"  Critic Model ID: {config.CRITIC_MODEL_ID}")
    print(f"  Base Model ID: {config.BASE_MODEL_ID}")
    print(f"  Question Bank Path: {config.QUESTION_BANK_PATH}")
    print(f"  Random Seed: {config.SEED}")
    print(f"  Max Sequence Length: {config.MAX_SEQ_LENGTH}")
    print(f"  Data Raw Dir: {config.DATA_RAW_DIR}")
    print(f"  Data Processed Dir: {config.DATA_PROCESSED_DIR}")
    print(f"  Data Results Dir: {config.DATA_RESULTS_DIR}")
    print(f"  State Dir: {config.STATE_DIR}")


if __name__ == "__main__":
    main()