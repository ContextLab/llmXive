"""
Environment configuration management for random seeds and model paths.

This module provides the SocraticConfig dataclass and utilities to load
configuration from environment variables, ensuring deterministic experiments
via random seed management and centralized model path configuration.
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
    Centralized configuration for the Socratic Transformers project.
    
    Attributes:
        seed (int): Random seed for reproducibility (default: 42).
        project_root (Path): Root directory of the project.
        data_root (Path): Directory containing raw, processed, and results data.
        model_root (Path): Directory for storing/downloading models.
        device (str): Target device ('cpu', 'cuda', 'mps').
        model_name (str): HuggingFace model identifier for the base model.
        critic_model_name (str): HuggingFace model identifier for the frozen critic.
        max_tokens (int): Maximum sequence length for tokenization.
        batch_size (int): Training batch size.
        gradient_accumulation_steps (int): Gradient accumulation steps.
        lora_rank (int): LoRA rank for fine-tuning.
        lora_alpha (int): LoRA alpha scaling factor.
        lora_dropout (float): LoRA dropout rate.
        quantization_4bit (bool): Enable 4-bit quantization.
        output_dir (Path): Directory for training outputs and checkpoints.
        logging_dir (Path): Directory for log files.
    """
    # Reproducibility
    seed: int = 42
    
    # Paths
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[3])
    data_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2] / "data")
    model_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2] / "models")
    output_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2] / "data" / "results")
    logging_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2] / "data" / "logs")
    
    # Model Configuration
    device: str = "cpu"
    model_name: str = "google/gemma-2b-it"  # Small base model for CPU constraints
    critic_model_name: str = "meta-llama/Llama-3-8B"  # Placeholder for frozen critic
    max_tokens: int = 2048
    
    # Training Configuration
    batch_size: int = 1
    gradient_accumulation_steps: int = 4
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.1
    quantization_4bit: bool = True
    
    # Data Configuration
    datasets: List[str] = field(default_factory=lambda: ["gsm8k", "math"])
    
    def __post_init__(self):
        """Ensure paths are Path objects and create directories if missing."""
        if isinstance(self.project_root, str):
            self.project_root = Path(self.project_root)
        if isinstance(self.data_root, str):
            self.data_root = Path(self.data_root)
        if isinstance(self.model_root, str):
            self.model_root = Path(self.model_root)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if isinstance(self.logging_dir, str):
            self.logging_dir = Path(self.logging_dir)
        
        # Ensure critical directories exist
        self.data_root.mkdir(parents=True, exist_ok=True)
        (self.data_root / "raw").mkdir(parents=True, exist_ok=True)
        (self.data_root / "processed").mkdir(parents=True, exist_ok=True)
        (self.data_root / "results").mkdir(parents=True, exist_ok=True)
        self.model_root.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logging_dir.mkdir(parents=True, exist_ok=True)

# Global configuration instance
_global_config: Optional[SocraticConfig] = None

def load_config_from_env() -> SocraticConfig:
    """
    Load configuration from environment variables, falling back to defaults.
    
    Returns:
        SocraticConfig: The populated configuration object.
    """
    config = SocraticConfig()
    
    # Override with environment variables if present
    if os.getenv("SOCRATIC_SEED"):
        config.seed = int(os.getenv("SOCRATIC_SEED"))
    
    if os.getenv("SOCRATIC_DEVICE"):
        config.device = os.getenv("SOCRATIC_DEVICE")
    
    if os.getenv("SOCRATIC_MODEL_NAME"):
        config.model_name = os.getenv("SOCRATIC_MODEL_NAME")
    
    if os.getenv("SOCRATIC_CRITIC_MODEL_NAME"):
        config.critic_model_name = os.getenv("SOCRATIC_CRITIC_MODEL_NAME")
    
    if os.getenv("SOCRATIC_MAX_TOKENS"):
        config.max_tokens = int(os.getenv("SOCRATIC_MAX_TOKENS"))
    
    if os.getenv("SOCRATIC_BATCH_SIZE"):
        config.batch_size = int(os.getenv("SOCRATIC_BATCH_SIZE"))
    
    if os.getenv("SOCRATIC_GRADIENT_ACCUMULATION_STEPS"):
        config.gradient_accumulation_steps = int(os.getenv("SOCRATIC_GRADIENT_ACCUMULATION_STEPS"))
    
    if os.getenv("SOCRATIC_LORA_RANK"):
        config.lora_rank = int(os.getenv("SOCRATIC_LORA_RANK"))
    
    if os.getenv("SOCRATIC_LORA_ALPHA"):
        config.lora_alpha = int(os.getenv("SOCRATIC_LORA_ALPHA"))
    
    if os.getenv("SOCRATIC_LORA_DROPOUT"):
        config.lora_dropout = float(os.getenv("SOCRATIC_LORA_DROPOUT"))
    
    if os.getenv("SOCRATIC_QUANTIZATION_4BIT"):
        config.quantization_4bit = os.getenv("SOCRATIC_QUANTIZATION_4BIT").lower() in ("true", "1", "yes")
    
    if os.getenv("SOCRATIC_DATA_ROOT"):
        config.data_root = Path(os.getenv("SOCRATIC_DATA_ROOT"))
    
    if os.getenv("SOCRATIC_MODEL_ROOT"):
        config.model_root = Path(os.getenv("SOCRATIC_MODEL_ROOT"))
    
    if os.getenv("SOCRATIC_OUTPUT_DIR"):
        config.output_dir = Path(os.getenv("SOCRATIC_OUTPUT_DIR"))
    
    if os.getenv("SOCRATIC_LOGGING_DIR"):
        config.logging_dir = Path(os.getenv("SOCRATIC_LOGGING_DIR"))
    
    return config

def get_config() -> SocraticConfig:
    """
    Get the global configuration instance, initializing it if necessary.
    
    Returns:
        SocraticConfig: The global configuration object.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
        set_seed(_global_config.seed)
    return _global_config

def set_global_config(config: SocraticConfig) -> None:
    """
    Set the global configuration instance explicitly.
    
    Args:
        config: The configuration object to set as global.
    """
    global _global_config
    _global_config = config
    set_seed(config.seed)

def set_seed(seed: int) -> None:
    """
    Set random seeds for reproducibility across Python, NumPy, and PyTorch.
    
    Args:
        seed: The random seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # PyTorch not installed

def init_project() -> SocraticConfig:
    """
    Initialize the project configuration and ensure directory structure exists.
    
    Returns:
        SocraticConfig: The initialized configuration object.
    """
    config = load_config_from_env()
    set_global_config(config)
    return config

def main():
    """CLI entry point to print current configuration."""
    config = get_config()
    print("Socratic Configuration:")
    print(f"  Seed: {config.seed}")
    print(f"  Device: {config.device}")
    print(f"  Model: {config.model_name}")
    print(f"  Critic Model: {config.critic_model_name}")
    print(f"  Max Tokens: {config.max_tokens}")
    print(f"  Batch Size: {config.batch_size}")
    print(f"  Data Root: {config.data_root}")
    print(f"  Output Dir: {config.output_dir}")

if __name__ == "__main__":
    main()
