"""
Environment configuration management for random seeds and model paths.

This module provides a centralized configuration system for the Socratic Transformers
project, handling random seed initialization, model path resolution, and
environment variable management.
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
    Central configuration dataclass for the Socratic Transformers project.

    Attributes:
        seed: Random seed for reproducibility across numpy, random, and torch.
        project_root: Root directory of the project.
        data_dir: Directory for raw and processed data.
        results_dir: Directory for experiment results and logs.
        model_cache_dir: Directory for cached model weights.
        base_model_name: HuggingFace model identifier for the base model.
        critic_model_name: HuggingFace model identifier for the frozen critic.
        device: Target device ('cpu', 'cuda', 'mps').
        max_tokens: Maximum sequence length for tokenization.
        batch_size: Training batch size.
        gradient_accumulation_steps: Number of steps for gradient accumulation.
        quantization_bits: Number of bits for quantization (4 or 8).
        lora_rank: LoRA attention dimension.
        lora_alpha: LoRA alpha scaling parameter.
        lora_dropout: Dropout rate for LoRA layers.
        logging_dir: Directory for experiment logs.
    """
    seed: int = 42
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.parent)
    data_dir: Path = field(default_factory=lambda: Path("data"))
    results_dir: Path = field(default_factory=lambda: Path("data/results"))
    model_cache_dir: Optional[Path] = None
    base_model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    critic_model_name: str = "TinyLlama/TinyLlama-1.1B-Instruct-v0.2"
    device: str = "cpu"
    max_tokens: int = 2048
    batch_size: int = 1
    gradient_accumulation_steps: int = 4
    quantization_bits: int = 4
    lora_rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    logging_dir: Path = field(default_factory=lambda: Path("logs"))
    # Additional paths relative to project root
    raw_data_dir: Optional[Path] = None
    processed_data_dir: Optional[Path] = None

    def __post_init__(self):
        """Initialize paths relative to project root if not absolute."""
        if not self.project_root.is_absolute():
            # Resolve relative to current working directory if not absolute
            self.project_root = Path.cwd() / self.project_root

        # Resolve data directories relative to project root
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
        if not self.data_dir.is_absolute():
            self.data_dir = self.project_root / self.data_dir

        if isinstance(self.results_dir, str):
            self.results_dir = Path(self.results_dir)
        if not self.results_dir.is_absolute():
            self.results_dir = self.project_root / self.results_dir

        if isinstance(self.logging_dir, str):
            self.logging_dir = Path(self.logging_dir)
        if not self.logging_dir.is_absolute():
            self.logging_dir = self.project_root / self.logging_dir

        # Set default sub-directories
        self.raw_data_dir = self.data_dir / "raw"
        self.processed_data_dir = self.data_dir / "processed"

        # Set model cache dir if not provided
        if self.model_cache_dir is None:
            self.model_cache_dir = self.project_root / "model_cache"

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary."""
        return {
            "seed": self.seed,
            "project_root": str(self.project_root),
            "data_dir": str(self.data_dir),
            "results_dir": str(self.results_dir),
            "model_cache_dir": str(self.model_cache_dir),
            "base_model_name": self.base_model_name,
            "critic_model_name": self.critic_model_name,
            "device": self.device,
            "max_tokens": self.max_tokens,
            "batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "quantization_bits": self.quantization_bits,
            "lora_rank": self.lora_rank,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "logging_dir": str(self.logging_dir),
        }

    def save_to_file(self, path: Path) -> None:
        """Save configuration to a JSON file."""
        import json
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, path: Path) -> "SocraticConfig":
        """Load configuration from a JSON file."""
        import json
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Convert string paths back to Path objects
        for key in ["project_root", "data_dir", "results_dir", "model_cache_dir", "logging_dir"]:
            if key in data and isinstance(data[key], str):
                data[key] = Path(data[key])
        return cls(**data)


# Global configuration instance
_global_config: Optional[SocraticConfig] = None


def load_config_from_env() -> SocraticConfig:
    """
    Load configuration from environment variables.

    Environment variables are prefixed with 'SROCTIC_' and mapped to config fields.
    Example: SROCTIC_SEED=123 -> config.seed = 123

    Returns:
        SocraticConfig instance with values from environment.
    """
    env_map = {
        "seed": "SROCTIC_SEED",
        "base_model_name": "SROCTIC_BASE_MODEL",
        "critic_model_name": "SROCTIC_CRITIC_MODEL",
        "device": "SROCTIC_DEVICE",
        "max_tokens": "SROCTIC_MAX_TOKENS",
        "batch_size": "SROCTIC_BATCH_SIZE",
        "gradient_accumulation_steps": "SROCTIC_GRAD_ACCUM",
        "quantization_bits": "SROCTIC_QUANT_BITS",
        "lora_rank": "SROCTIC_LORA_RANK",
        "lora_alpha": "SROCTIC_LORA_ALPHA",
        "lora_dropout": "SROCTIC_LORA_DROPOUT",
    }

    config_kwargs = {}
    for attr, env_var in env_map.items():
        value = os.getenv(env_var)
        if value is not None:
            # Type conversion based on expected type
            if attr in ["seed", "max_tokens", "batch_size", "gradient_accumulation_steps", "quantization_bits", "lora_rank"]:
                config_kwargs[attr] = int(value)
            elif attr in ["lora_dropout"]:
                config_kwargs[attr] = float(value)
            else:
                config_kwargs[attr] = value

    # Handle path-specific environment variables
    if "SROCTIC_PROJECT_ROOT" in os.environ:
        config_kwargs["project_root"] = Path(os.environ["SROCTIC_PROJECT_ROOT"])
    if "SROCTIC_DATA_DIR" in os.environ:
        config_kwargs["data_dir"] = Path(os.environ["SROCTIC_DATA_DIR"])
    if "SROCTIC_RESULTS_DIR" in os.environ:
        config_kwargs["results_dir"] = Path(os.environ["SROCTIC_RESULTS_DIR"])
    if "SROCTIC_LOGGING_DIR" in os.environ:
        config_kwargs["logging_dir"] = Path(os.environ["SROCTIC_LOGGING_DIR"])

    return SocraticConfig(**config_kwargs)


def get_config() -> SocraticConfig:
    """
    Get the global configuration instance.

    If no global config is set, loads from environment variables.

    Returns:
        SocraticConfig instance.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
    return _global_config


def set_global_config(config: SocraticConfig) -> None:
    """
    Set the global configuration instance.

    Args:
        config: SocraticConfig instance to set as global.
    """
    global _global_config
    _global_config = config


def set_seed(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility.

    Sets seeds for:
    - Python's random module
    - NumPy
    - PyTorch (if available)

    Args:
        seed: Random seed value. If None, uses the seed from global config.
    """
    if seed is None:
        seed = get_config().seed

    random.seed(seed)
    np.random.seed(seed)

    # Set PyTorch seeds if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior (may impact performance)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass  # PyTorch not installed


def init_project(config: Optional[SocraticConfig] = None) -> SocraticConfig:
    """
    Initialize the project structure based on configuration.

    Creates necessary directories for data, results, and logs.

    Args:
        config: Optional SocraticConfig instance. If None, uses global config.

    Returns:
        The initialized SocraticConfig instance.
    """
    if config is None:
        config = get_config()
    else:
        set_global_config(config)

    # Create directories
    dirs_to_create = [
        config.data_dir,
        config.raw_data_dir,
        config.processed_data_dir,
        config.results_dir,
        config.logging_dir,
        config.model_cache_dir,
    ]

    for dir_path in dirs_to_create:
        if dir_path:
            dir_path.mkdir(parents=True, exist_ok=True)

    return config


def main() -> None:
    """
    Main entry point for command-line usage.

    Demonstrates configuration loading and project initialization.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Socratic Transformers Configuration Manager")
    parser.add_argument("--init", action="store_true", help="Initialize project directories")
    parser.add_argument("--save", type=str, help="Save config to a JSON file")
    parser.add_argument("--seed", type=int, help="Override random seed")
    parser.add_argument("--device", type=str, help="Override target device")
    args = parser.parse_args()

    # Load config from environment
    config = load_config_from_env()

    # Apply command-line overrides
    if args.seed is not None:
        config.seed = args.seed
    if args.device is not None:
        config.device = args.device

    # Set global config
    set_global_config(config)

    print(f"Configuration loaded:")
    print(f"  Seed: {config.seed}")
    print(f"  Device: {config.device}")
    print(f"  Base Model: {config.base_model_name}")
    print(f"  Critic Model: {config.critic_model_name}")
    print(f"  Data Dir: {config.data_dir}")
    print(f"  Results Dir: {config.results_dir}")

    if args.init:
        init_project(config)
        print(f"Project directories initialized at {config.project_root}")

    if args.save:
        config.save_to_file(Path(args.save))
        print(f"Configuration saved to {args.save}")

    # Set seeds
    set_seed(config.seed)
    print(f"Random seeds set to {config.seed}")


if __name__ == "__main__":
    main()