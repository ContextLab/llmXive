"""
Environment configuration management for random seeds and model paths.

This module provides a centralized configuration system for the Socratic Transformers project,
handling random seeds for reproducibility, model paths, and other environment variables.
"""

import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent

@dataclass
class SocraticConfig:
    """
    Central configuration class for the Socratic Transformers project.

    Attributes:
        seed: Random seed for reproducibility (default: 42)
        project_root: Root directory of the project
        data_dir: Directory for data files
        model_cache_dir: Directory for cached models
        critic_model_id: HuggingFace model ID for the critic model
        base_model_id: HuggingFace model ID for the base model
        output_dir: Directory for output files
        log_level: Logging level (default: "INFO")
        max_tokens: Maximum tokens for generation (default: 512)
        batch_size: Training batch size (default: 1)
        gradient_accumulation_steps: Gradient accumulation steps (default: 4)
        learning_rate: Learning rate (default: 2e-5)
        num_epochs: Number of training epochs (default: 3)
        use_4bit: Whether to use 4-bit quantization (default: True)
        cpu_offload: Whether to use CPU offloading (default: True)
    """
    seed: int = 42
    project_root: Path = field(default_factory=lambda: PROJECT_ROOT)
    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data")
    model_cache_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "models")
    critic_model_id: str = "TinyLlama/TinyLlama-1.1B-Chat-v0.2"
    base_model_id: str = "TinyLlama/TinyLlama-1.1B-Chat-v0.2"
    output_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "data" / "results")
    log_level: str = "INFO"
    max_tokens: int = 512
    batch_size: int = 1
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-5
    num_epochs: int = 3
    use_4bit: bool = True
    cpu_offload: bool = True
    # Additional fields for dataset management
    datasets: List[str] = field(default_factory=lambda: ["gsm8k", "math"])
    # Ablation configuration
    ablation_placeholder: str = "The variable X is defined as Y, which implies Z, therefore..."

    def __post_init__(self):
        """Initialize paths and ensure directories exist."""
        # Ensure project root is absolute
        self.project_root = self.project_root.resolve()
        self.data_dir = self.data_dir.resolve()
        self.model_cache_dir = self.model_cache_dir.resolve()
        self.output_dir = self.output_dir.resolve()

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "seed": self.seed,
            "project_root": str(self.project_root),
            "data_dir": str(self.data_dir),
            "model_cache_dir": str(self.model_cache_dir),
            "critic_model_id": self.critic_model_id,
            "base_model_id": self.base_model_id,
            "output_dir": str(self.output_dir),
            "log_level": self.log_level,
            "max_tokens": self.max_tokens,
            "batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "learning_rate": self.learning_rate,
            "num_epochs": self.num_epochs,
            "use_4bit": self.use_4bit,
            "cpu_offload": self.cpu_offload,
            "datasets": self.datasets,
            "ablation_placeholder": self.ablation_placeholder,
        }

# Global configuration instance
_global_config: Optional[SocraticConfig] = None

def load_config_from_env() -> SocraticConfig:
    """
    Load configuration from environment variables.

    Returns:
        SocraticConfig instance populated with environment variables
    """
    config = SocraticConfig()

    # Override with environment variables if present
    if seed := os.getenv("SOCRATIC_SEED"):
        config.seed = int(seed)

    if log_level := os.getenv("SOCRATIC_LOG_LEVEL"):
        config.log_level = log_level

    if max_tokens := os.getenv("SOCRATIC_MAX_TOKENS"):
        config.max_tokens = int(max_tokens)

    if batch_size := os.getenv("SOCRATIC_BATCH_SIZE"):
        config.batch_size = int(batch_size)

    if gradient_accumulation_steps := os.getenv("SOCRATIC_GRADIENT_ACCUMULATION"):
        config.gradient_accumulation_steps = int(gradient_accumulation_steps)

    if learning_rate := os.getenv("SOCRATIC_LEARNING_RATE"):
        config.learning_rate = float(learning_rate)

    if num_epochs := os.getenv("SOCRATIC_NUM_EPOCHS"):
        config.num_epochs = int(num_epochs)

    if critic_model_id := os.getenv("SOCRATIC_CRITIC_MODEL"):
        config.critic_model_id = critic_model_id

    if base_model_id := os.getenv("SOCRATIC_BASE_MODEL"):
        config.base_model_id = base_model_id

    if use_4bit := os.getenv("SOCRATIC_USE_4BIT"):
        config.use_4bit = use_4bit.lower() in ("true", "1", "yes")

    if cpu_offload := os.getenv("SOCRATIC_CPU_OFFLOAD"):
        config.cpu_offload = cpu_offload.lower() in ("true", "1", "yes")

    if datasets_str := os.getenv("SOCRATIC_DATASETS"):
        config.datasets = [d.strip() for d in datasets_str.split(",")]

    return config

def get_config() -> SocraticConfig:
    """
    Get the global configuration instance.

    Returns:
        The global SocraticConfig instance, initializing it if necessary
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
    return _global_config

def set_global_config(config: SocraticConfig) -> None:
    """
    Set the global configuration instance.

    Args:
        config: The SocraticConfig instance to set as global
    """
    global _global_config
    _global_config = config

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility.

    Args:
        seed: Random seed to use. If None, uses the seed from global config
    """
    if seed is None:
        seed = get_config().seed

    random.seed(seed)
    np.random.seed(seed)
    # If torch is available, set its seed too
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def init_project() -> None:
    """
    Initialize project directories and global configuration.

    Creates necessary directories if they don't exist.
    """
    config = get_config()

    # Create directories
    config.data_dir.mkdir(parents=True, exist_ok=True)
    (config.data_dir / "raw").mkdir(exist_ok=True)
    (config.data_dir / "processed").mkdir(exist_ok=True)
    (config.data_dir / "results").mkdir(exist_ok=True)
    config.model_cache_dir.mkdir(parents=True, exist_ok=True)
    config.output_dir.mkdir(parents=True, exist_ok=True)

    # Set global seed
    set_seed(config.seed)

def main() -> None:
    """
    Main entry point for configuration management.

    Prints current configuration and initializes project directories.
    """
    print("Initializing Socratic Transformers project...")
    init_project()

    config = get_config()
    print(f"Configuration loaded:")
    for key, value in config.to_dict().items():
        print(f"  {key}: {value}")

    print("\nProject directories initialized.")
    print(f"  Data directory: {config.data_dir}")
    print(f"  Model cache: {config.model_cache_dir}")
    print(f"  Output directory: {config.output_dir}")

if __name__ == "__main__":
    main()
