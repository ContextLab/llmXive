"""
Environment configuration management for Socratic Transformers project.

Handles random seeds, model paths, and experimental parameters.
Model IDs are required and must be provided via environment variables
or a config file to allow experimental flexibility per FR-003.
"""

import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np


@dataclass
class SocraticConfig:
    """
    Main configuration class for the Socratic Transformers pipeline.
    
    Attributes:
        CRITIC_MODEL_ID: Required. ID of the frozen critic model for adversarial critique.
        BASE_MODEL_ID: Required. ID of the base model for answer generation and fine-tuning.
        QUESTION_BANK_PATH: Optional. Path to a local question bank file.
        ADVERSARIAL_PROMPT_TEMPLATE: Template string for generating critique prompts.
        SELECTION_THRESHOLD: Float threshold for negative selection (similarity score).
        RANDOM_SEED: Integer seed for reproducibility.
    """
    CRITIC_MODEL_ID: str = field(
        default_factory=lambda: os.environ.get("CRITIC_MODEL_ID")
    )
    BASE_MODEL_ID: str = field(
        default_factory=lambda: os.environ.get("BASE_MODEL_ID")
    )
    QUESTION_BANK_PATH: Optional[str] = None
    ADVERSARIAL_PROMPT_TEMPLATE: str = "Identify logical contradictions in: {answer}"
    SELECTION_THRESHOLD: float = 0.85
    RANDOM_SEED: int = 42
    
    # Additional runtime paths
    PROJECT_ROOT: Path = field(
        default_factory=lambda: Path(__file__).resolve().parents[3]
    )
    DATA_RAW_DIR: Path = field(init=False)
    DATA_PROCESSED_DIR: Path = field(init=False)
    DATA_RESULTS_DIR: Path = field(init=False)
    STATE_DIR: Path = field(init=False)
    
    def __post_init__(self):
        """Initialize derived paths after dataclass initialization."""
        self.DATA_RAW_DIR = self.PROJECT_ROOT / "data" / "raw"
        self.DATA_PROCESSED_DIR = self.PROJECT_ROOT / "data" / "processed"
        self.DATA_RESULTS_DIR = self.PROJECT_ROOT / "data" / "results"
        self.STATE_DIR = self.PROJECT_ROOT / "state"
        
        # Ensure model IDs are set
        if not self.CRITIC_MODEL_ID:
            raise ValueError(
                "CRITIC_MODEL_ID must be set via environment variable "
                "or config file. Set CRITIC_MODEL_ID=<model_id>."
            )
        if not self.BASE_MODEL_ID:
            raise ValueError(
                "BASE_MODEL_ID must be set via environment variable "
                "or config file. Set BASE_MODEL_ID=<model_id>."
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration to a dictionary."""
        return {
            "CRITIC_MODEL_ID": self.CRITIC_MODEL_ID,
            "BASE_MODEL_ID": self.BASE_MODEL_ID,
            "QUESTION_BANK_PATH": self.QUESTION_BANK_PATH,
            "ADVERSARIAL_PROMPT_TEMPLATE": self.ADVERSARIAL_PROMPT_TEMPLATE,
            "SELECTION_THRESHOLD": self.SELECTION_THRESHOLD,
            "RANDOM_SEED": self.RANDOM_SEED,
            "PROJECT_ROOT": str(self.PROJECT_ROOT),
            "DATA_RAW_DIR": str(self.DATA_RAW_DIR),
            "DATA_PROCESSED_DIR": str(self.DATA_PROCESSED_DIR),
            "DATA_RESULTS_DIR": str(self.DATA_RESULTS_DIR),
            "STATE_DIR": str(self.STATE_DIR),
        }

# Global configuration instance
_global_config: Optional[SocraticConfig] = None


def get_config() -> SocraticConfig:
    """
    Retrieve the global configuration instance.
    
    Returns:
        The active SocraticConfig instance.
        
    Raises:
        ValueError: If the configuration has not been initialized.
    """
    if _global_config is None:
        raise ValueError(
            "Configuration not initialized. Call init_project() or set_config() first."
        )
    return _global_config


def set_global_config(config: SocraticConfig) -> None:
    """
    Set the global configuration instance.
    
    Args:
        config: The SocraticConfig instance to set as global.
    """
    global _global_config
    _global_config = config


def load_config_from_env() -> SocraticConfig:
    """
    Load configuration from environment variables.
    
    Environment variables:
        CRITIC_MODEL_ID: Model ID for the critic.
        BASE_MODEL_ID: Model ID for the base model.
        QUESTION_BANK_PATH: Optional path to question bank.
        ADVERSARIAL_PROMPT_TEMPLATE: Template for critique prompts.
        SELECTION_THRESHOLD: Threshold for negative selection.
        RANDOM_SEED: Random seed for reproducibility.
        
    Returns:
        A new SocraticConfig instance populated from environment variables.
    """
    critic_id = os.environ.get("CRITIC_MODEL_ID")
    base_id = os.environ.get("BASE_MODEL_ID")
    question_bank = os.environ.get("QUESTION_BANK_PATH")
    prompt_template = os.environ.get(
        "ADVERSARIAL_PROMPT_TEMPLATE",
        "Identify logical contradictions in: {answer}"
    )
    threshold_str = os.environ.get("SELECTION_THRESHOLD", "0.85")
    seed_str = os.environ.get("RANDOM_SEED", "42")
    
    try:
        threshold = float(threshold_str)
    except ValueError:
        raise ValueError(f"SELECTION_THRESHOLD must be a float, got: {threshold_str}")
    
    try:
        seed = int(seed_str)
    except ValueError:
        raise ValueError(f"RANDOM_SEED must be an integer, got: {seed_str}")
    
    return SocraticConfig(
        CRITIC_MODEL_ID=critic_id,
        BASE_MODEL_ID=base_id,
        QUESTION_BANK_PATH=question_bank,
        ADVERSARIAL_PROMPT_TEMPLATE=prompt_template,
        SELECTION_THRESHOLD=threshold,
        RANDOM_SEED=seed
    )

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility across all libraries.
    
    Args:
        seed: The seed value. If None, uses the seed from the global config.
    """
    if seed is None:
        config = get_config()
        seed = config.RANDOM_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    if 'torch' in globals() or 'torch' in __import__('sys').modules:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

def init_project() -> SocraticConfig:
    """
    Initialize the project by loading configuration from environment
    and setting up the global config instance.
    
    Returns:
        The initialized SocraticConfig instance.
    """
    config = load_config_from_env()
    set_global_config(config)
    set_seed(config.RANDOM_SEED)
    
    # Ensure directories exist
    for dir_path in [config.DATA_RAW_DIR, config.DATA_PROCESSED_DIR, 
                     config.DATA_RESULTS_DIR, config.STATE_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return config

def main():
    """Entry point for testing configuration loading."""
    try:
        config = init_project()
        print(f"Configuration loaded successfully:")
        print(f"  CRITIC_MODEL_ID: {config.CRITIC_MODEL_ID}")
        print(f"  BASE_MODEL_ID: {config.BASE_MODEL_ID}")
        print(f"  SELECTION_THRESHOLD: {config.SELECTION_THRESHOLD}")
        print(f"  RANDOM_SEED: {config.RANDOM_SEED}")
    except ValueError as e:
        print(f"Configuration error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())