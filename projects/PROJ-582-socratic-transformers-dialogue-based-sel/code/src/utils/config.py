"""
Environment configuration management for random seeds and model paths.

This module provides a centralized configuration system for the Socratic Transformers
project, handling:
- Random seed management for reproducibility (Python, NumPy, PyTorch)
- Model path configuration from environment variables
- Global configuration state management
- Data directory paths
"""

import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np


@dataclass
class SocraticConfig:
    """
    Central configuration class for the Socratic Transformers project.

    Attributes:
        seed: Random seed for reproducibility (default: 42)
        base_model_path: Path to the base model for fine-tuning
        lora_model_path: Path to the LoRA adapter (if applicable)
        data_dir: Root directory for data files
        output_dir: Directory for experiment outputs and logs
        device: Target device ('cpu', 'cuda', 'mps')
        max_seq_length: Maximum sequence length for tokenization
        batch_size: Training batch size
        gradient_accumulation_steps: Number of steps for gradient accumulation
        learning_rate: Learning rate for optimization
        num_epochs: Number of training epochs
        use_4bit_quantization: Whether to use 4-bit quantization for memory efficiency
        fallback_model_path: Path to fallback model if OOM occurs
    """
    seed: int = 42
    base_model_path: str = "microsoft/phi-1.5"
    lora_model_path: Optional[str] = None
    data_dir: str = "data"
    output_dir: str = "data/results"
    device: str = "cpu"
    max_seq_length: int = 512
    batch_size: int = 2
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    num_epochs: int = 3
    use_4bit_quantization: bool = True
    fallback_model_path: str = "microsoft/phi-1.5"  # Fallback to same model or smaller variant
    log_dir: str = "data/logs"
    processed_data_dir: str = "data/processed"
    raw_data_dir: str = "data/raw"

    def __post_init__(self):
        """Validate and normalize paths after initialization."""
        self.data_dir = Path(self.data_dir)
        self.output_dir = Path(self.output_dir)
        self.log_dir = Path(self.log_dir)
        self.processed_data_dir = Path(self.processed_data_dir)
        self.raw_data_dir = Path(self.raw_data_dir)
        self.base_model_path = Path(self.base_model_path)
        self.fallback_model_path = Path(self.fallback_model_path)

        if self.lora_model_path:
            self.lora_model_path = Path(self.lora_model_path)

    def set_seeds(self):
        """
        Set random seeds for Python, NumPy, and PyTorch to ensure reproducibility.

        This method must be called after config initialization to ensure all
        random number generators are seeded consistently.
        """
        random.seed(self.seed)
        np.random.seed(self.seed)
        try:
            import torch
            torch.manual_seed(self.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(self.seed)
                torch.cuda.manual_seed_all(self.seed)
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
        except ImportError:
            # PyTorch not installed, skip torch seeding
            pass

    def get_model_paths(self) -> Dict[str, str]:
        """
        Get a dictionary of all model-related paths.

        Returns:
            Dict mapping model type names to their configured paths.
        """
        paths = {
            "base_model": str(self.base_model_path),
            "fallback_model": str(self.fallback_model_path),
        }
        if self.lora_model_path:
            paths["lora_adapter"] = str(self.lora_model_path)
        return paths

    def get_data_paths(self) -> Dict[str, str]:
        """
        Get a dictionary of all data-related paths.

        Returns:
            Dict mapping data type names to their configured paths.
        """
        return {
            "raw": str(self.raw_data_dir),
            "processed": str(self.processed_data_dir),
            "results": str(self.output_dir),
            "logs": str(self.log_dir),
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a dictionary for serialization.

        Returns:
            Dictionary representation of the configuration.
        """
        result = {}
        for key, value in self.__dataclass_fields__.items():
            val = getattr(self, key)
            if isinstance(val, Path):
                val = str(val)
            result[key] = val
        return result


# Global configuration instance
_global_config: Optional[SocraticConfig] = None


def load_config_from_env() -> SocraticConfig:
    """
    Load configuration from environment variables.

    Environment variables:
        SEED: Random seed (default: 42)
        BASE_MODEL_PATH: Path to base model (default: microsoft/phi-1.5)
        DATA_DIR: Root data directory (default: data)
        OUTPUT_DIR: Output directory (default: data/results)
        DEVICE: Target device (default: cpu)
        MAX_SEQ_LENGTH: Maximum sequence length (default: 512)
        BATCH_SIZE: Training batch size (default: 2)
        GRADIENT_ACCUMULATION_STEPS: Gradient accumulation steps (default: 4)
        LEARNING_RATE: Learning rate (default: 2e-4)
        NUM_EPOCHS: Number of epochs (default: 3)
        USE_4BIT_QUANTIZATION: Enable 4-bit quantization (default: true)
        FALLBACK_MODEL_PATH: Path to fallback model (default: microsoft/phi-1.5)
        LOG_DIR: Log directory (default: data/logs)

    Returns:
        SocraticConfig instance populated from environment variables.
    """
    def get_env_int(key: str, default: int) -> int:
        val = os.environ.get(key)
        return int(val) if val is not None else default

    def get_env_float(key: str, default: float) -> float:
        val = os.environ.get(key)
        return float(val) if val is not None else default

    def get_env_str(key: str, default: str) -> str:
        return os.environ.get(key, default)

    def get_env_bool(key: str, default: bool) -> bool:
        val = os.environ.get(key)
        if val is None:
            return default
        return val.lower() in ("true", "1", "yes", "on")

    config = SocraticConfig(
        seed=get_env_int("SEED", 42),
        base_model_path=get_env_str("BASE_MODEL_PATH", "microsoft/phi-1.5"),
        data_dir=get_env_str("DATA_DIR", "data"),
        output_dir=get_env_str("OUTPUT_DIR", "data/results"),
        device=get_env_str("DEVICE", "cpu"),
        max_seq_length=get_env_int("MAX_SEQ_LENGTH", 512),
        batch_size=get_env_int("BATCH_SIZE", 2),
        gradient_accumulation_steps=get_env_int("GRADIENT_ACCUMULATION_STEPS", 4),
        learning_rate=get_env_float("LEARNING_RATE", 2e-4),
        num_epochs=get_env_int("NUM_EPOCHS", 3),
        use_4bit_quantization=get_env_bool("USE_4BIT_QUANTIZATION", True),
        fallback_model_path=get_env_str("FALLBACK_MODEL_PATH", "microsoft/phi-1.5"),
        log_dir=get_env_str("LOG_DIR", "data/logs"),
    )

    # Optional: Load LoRA path if set
    lora_path = os.environ.get("LORA_MODEL_PATH")
    if lora_path:
        config.lora_model_path = lora_path

    return config


def get_config() -> SocraticConfig:
    """
    Get the global configuration instance.

    If no global config exists, loads from environment variables.

    Returns:
        The global SocraticConfig instance.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
    return _global_config


def set_global_config(config: SocraticConfig) -> None:
    """
    Set the global configuration instance.

    Args:
        config: The SocraticConfig instance to set as global.
    """
    global _global_config
    _global_config = config


def ensure_directories(config: Optional[SocraticConfig] = None) -> None:
    """
    Ensure all required directories exist.

    Args:
        config: Optional config instance. If None, uses the global config.
    """
    if config is None:
        config = get_config()

    directories = [
        config.data_dir,
        config.output_dir,
        config.log_dir,
        config.processed_data_dir,
        config.raw_data_dir,
    ]

    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)


# Convenience function to initialize the project configuration
def init_project(seed: Optional[int] = None) -> SocraticConfig:
    """
    Initialize the project configuration and set random seeds.

    Args:
        seed: Optional seed value. If None, uses environment or default.

    Returns:
        The initialized SocraticConfig instance.
    """
    config = load_config_from_env()
    if seed is not None:
        config.seed = seed

    set_global_config(config)
    config.set_seeds()
    ensure_directories(config)

    return config