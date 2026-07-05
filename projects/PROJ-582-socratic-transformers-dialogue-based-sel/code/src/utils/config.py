"""
Environment configuration management for random seeds and model paths.

This module provides a centralized configuration class to manage:
- Random seeds for reproducibility across numpy, torch, and random modules.
- Model paths for base models and LoRA adapters.
- Hyperparameters and environment-specific settings.

It adheres to the project's constraint of CPU-only execution and low-bit
quantization where applicable.
"""

import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@dataclass
class SocraticConfig:
    """
    Centralized configuration container for the Socratic Transformers project.

    Attributes:
        seed (int): Global random seed for reproducibility.
        project_root (Path): Absolute path to the project root.
        data_dir (Path): Path to the data directory.
        model_name (str): HuggingFace model identifier for the base model.
        model_path (Optional[Path]): Local path to a downloaded model (if not using HF hub).
        lora_adapter_path (Optional[Path]): Path to LoRA weights.
        max_seq_length (int): Maximum sequence length for input processing.
        batch_size (int): Training batch size (constrained to <= 2 for CPU).
        gradient_accumulation_steps (int): Steps for gradient accumulation.
        quantization_bits (int): Bits for quantization (4 for CPU efficiency).
        device (str): Target device ('cpu' or 'cuda').
        output_dir (Path): Directory for logs, checkpoints, and results.
    """

    seed: int = 42
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[3])
    
    # Data paths
    data_dir: Path = field(default_factory=lambda: Path("data"))
    
    # Model configuration
    model_name: str = "microsoft/phi-1.5"  # Default to 1.5B for CPU constraints
    model_path: Optional[Path] = None
    lora_adapter_path: Optional[Path] = None
    
    # Training hyperparameters
    max_seq_length: int = 512
    batch_size: int = 2
    gradient_accumulation_steps: int = 4
    quantization_bits: int = 4  # 4-bit quantization for memory efficiency
    
    # Environment
    device: str = "cpu"
    output_dir: Path = field(default_factory=lambda: Path("data/results"))
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    def __post_init__(self):
        """Resolve relative paths to absolute paths based on project root."""
        if not self.project_root.is_absolute():
            self.project_root = self.project_root.resolve()
        
        self.data_dir = self.project_root / self.data_dir
        self.output_dir = self.project_root / self.output_dir
        
        if self.model_path and not self.model_path.is_absolute():
            self.model_path = self.project_root / self.model_path
        
        if self.lora_adapter_path and not self.lora_adapter_path.is_absolute():
            self.lora_adapter_path = self.project_root / self.lora_adapter_path

        if self.log_file and not self.log_file.is_absolute():
            self.log_file = self.project_root / self.log_file

    def set_seed(self):
        """
        Set random seeds for reproducibility across all relevant libraries.
        
        This ensures that experiments are deterministic given the same seed.
        """
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        if TORCH_AVAILABLE:
            torch.manual_seed(self.seed)
            if self.device == "cuda":
                torch.cuda.manual_seed_all(self.seed)
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary for logging or serialization."""
        return {
            "seed": self.seed,
            "model_name": self.model_name,
            "model_path": str(self.model_path) if self.model_path else None,
            "max_seq_length": self.max_seq_length,
            "batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "quantization_bits": self.quantization_bits,
            "device": self.device,
            "data_dir": str(self.data_dir),
            "output_dir": str(self.output_dir),
        }


def load_config_from_env() -> SocraticConfig:
    """
    Load configuration from environment variables with sensible defaults.
    
    Environment variables:
        SROCATIC_SEED: Random seed (default: 42)
        SROCATIC_MODEL_NAME: HuggingFace model name (default: microsoft/phi-1.5)
        SROCATIC_MAX_SEQ_LENGTH: Max sequence length (default: 512)
        SROCATIC_BATCH_SIZE: Batch size (default: 2)
        SROCATIC_DEVICE: Device to use (default: cpu)
    """
    seed = int(os.getenv("SROCATIC_SEED", 42))
    model_name = os.getenv("SROCATIC_MODEL_NAME", "microsoft/phi-1.5")
    max_seq_length = int(os.getenv("SROCATIC_MAX_SEQ_LENGTH", 512))
    batch_size = int(os.getenv("SROCATIC_BATCH_SIZE", 2))
    device = os.getenv("SROCATIC_DEVICE", "cpu")
    
    # Ensure batch size constraint for CPU
    if device == "cpu" and batch_size > 2:
        print(f"Warning: Batch size {batch_size} reduced to 2 for CPU execution.")
        batch_size = 2

    return SocraticConfig(
        seed=seed,
        model_name=model_name,
        max_seq_length=max_seq_length,
        batch_size=batch_size,
        device=device
    )


# Global config instance for easy access
_global_config: Optional[SocraticConfig] = None


def get_config() -> SocraticConfig:
    """
    Get the global configuration instance, initializing it if necessary.
    
    Returns:
        SocraticConfig: The global configuration object.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
        _global_config.set_seed()
    return _global_config


def set_global_config(config: SocraticConfig):
    """
    Set the global configuration instance explicitly.
    
    Args:
        config: The configuration object to set as global.
    """
    global _global_config
    _global_config = config
    _global_config.set_seed()
