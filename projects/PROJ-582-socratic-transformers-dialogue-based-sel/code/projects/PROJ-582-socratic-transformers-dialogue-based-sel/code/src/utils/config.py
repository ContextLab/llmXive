"""
Environment configuration management for the Socratic Transformers project.

This module centralizes configuration for random seeds, model paths, and
critical hyperparameters. It ensures reproducibility and provides a single
source of truth for model identifiers used across the pipeline.

Philosophical Note:
This configuration defines the "ordered operations" of the engine.
CRITIC_MODEL_ID and BASE_MODEL_ID are fixed parameters (punch-cards)
that determine the selection pressure and the subject of evolution,
respectively. They are not learned; they are instantiated.
"""

import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np

# Default Model Identifiers
# These are selected to fit within the 7GB RAM constraint with 4-bit quantization
# as per project constraints.
DEFAULT_CRITIC_MODEL_ID = "microsoft/phi-2"  # Small, capable, fits in quantized RAM
DEFAULT_BASE_MODEL_ID = "microsoft/phi-2"    # Using same for consistency in MVP, can be swapped

# Default Seeds
DEFAULT_SEED = 42

@dataclass
class SocraticConfig:
    """
    Central configuration container for the Socratic pipeline.

    Attributes:
        critic_model_id: HuggingFace model ID for the frozen critic (adversarial component).
        base_model_id: HuggingFace model ID for the base model to be fine-tuned.
        seed: Random seed for reproducibility across numpy, torch, and python.
        project_root: Path to the project root directory.
        data_root: Path to the data directory.
        results_root: Path to the results directory.
        max_tokens: Maximum sequence length for generation.
        temperature: Temperature for text generation (default 0.7 for revised answers).
        log_level: Logging level string.
    """
    critic_model_id: str = DEFAULT_CRITIC_MODEL_ID
    base_model_id: str = DEFAULT_BASE_MODEL_ID
    seed: int = DEFAULT_SEED
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent.parent)
    data_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent.parent / "data")
    results_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent.parent / "data" / "results")
    max_tokens: int = 512
    temperature: float = 0.7
    log_level: str = "INFO"
    
    # Additional hyperparameters for training/generation
    batch_size: int = 1
    gradient_accumulation_steps: int = 4
    max_retries: int = 3
    quality_gate_min_tokens: int = 20

    def __post_init__(self):
        # Ensure paths are Path objects
        if isinstance(self.project_root, str):
            self.project_root = Path(self.project_root)
        if isinstance(self.data_root, str):
            self.data_root = Path(self.data_root)
        if isinstance(self.results_root, str):
            self.results_root = Path(self.results_root)

        # Validate critical model IDs are not empty
        if not self.critic_model_id:
            raise ValueError("CRITIC_MODEL_ID cannot be empty")
        if not self.base_model_id:
            raise ValueError("BASE_MODEL_ID cannot be empty")

# Global configuration instance
_global_config: Optional[SocraticConfig] = None

def get_config() -> SocraticConfig:
    """
    Returns the global SocraticConfig instance.
    Initializes it with defaults if not yet set.
    """
    global _global_config
    if _global_config is None:
        _global_config = SocraticConfig()
    return _global_config

def set_global_config(config: SocraticConfig) -> None:
    """
    Sets the global configuration instance.
    Useful for overwriting defaults in tests or CLI execution.
    """
    global _global_config
    _global_config = config

def load_config_from_env() -> SocraticConfig:
    """
    Loads configuration from environment variables, falling back to defaults.
    
    Environment Variables:
        CRITIC_MODEL_ID: Model ID for the critic.
        BASE_MODEL_ID: Model ID for the base model.
        SEED: Random seed.
        MAX_TOKENS: Max sequence length.
        TEMPERATURE: Generation temperature.
    """
    critic_id = os.getenv("CRITIC_MODEL_ID", DEFAULT_CRITIC_MODEL_ID)
    base_id = os.getenv("BASE_MODEL_ID", DEFAULT_BASE_MODEL_ID)
    seed = int(os.getenv("SEED", DEFAULT_SEED))
    max_tok = int(os.getenv("MAX_TOKENS", 512))
    temp = float(os.getenv("TEMPERATURE", 0.7))
    
    config = SocraticConfig(
        critic_model_id=critic_id,
        base_model_id=base_id,
        seed=seed,
        max_tokens=max_tok,
        temperature=temp
    )
    set_global_config(config)
    return config

def set_seed(seed: Optional[int] = None) -> None:
    """
    Sets the random seed for reproducibility across all libraries.
    
    Args:
        seed: The seed value. If None, uses the seed from global config.
    """
    if seed is None:
        seed = get_config().seed
    
    random.seed(seed)
    np.random.seed(seed)
    
    # Attempt to set torch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # Torch not installed, skip

def init_project() -> SocraticConfig:
    """
    Initializes the project configuration from environment and sets seeds.
    Also ensures necessary directories exist based on config paths.
    """
    config = load_config_from_env()
    set_seed(config.seed)
    
    # Ensure data and results directories exist
    config.data_root.mkdir(parents=True, exist_ok=True)
    config.results_root.mkdir(parents=True, exist_ok=True)
    
    return config

def main():
    """
    CLI entry point to print current configuration.
    """
    config = init_project()
    print(f"Configuration Loaded:")
    print(f"  Critic Model: {config.critic_model_id}")
    print(f"  Base Model: {config.base_model_id}")
    print(f"  Seed: {config.seed}")
    print(f"  Max Tokens: {config.max_tokens}")
    print(f"  Temperature: {config.temperature}")
    print(f"  Data Root: {config.data_root}")
    print(f"  Results Root: {config.results_root}")

if __name__ == "__main__":
    main()