"""
Environment configuration management for Socratic Transformers project.

Defines global constants for model paths, random seeds, and runtime settings.
Supports loading from environment variables for flexible deployment.
"""
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List
import numpy as np

# Core Model Identifiers
# These are the frozen models used for the Generator and Critic roles.
# Generator: Larger model for answer generation and revision.
# Critic: Smaller, frozen model for critique generation.
GENERATOR_MODEL_ID: str = "google/flan-t5-base"
CRITIC_MODEL_ID: str = "google/flan-t5-small"

# Random Seeds for reproducibility
DEFAULT_SEED: int = 42
NumpySeed = DEFAULT_SEED
TorchSeed = DEFAULT_SEED
RandomSeed = DEFAULT_SEED

# Path Constants
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR: Path = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS_DIR: Path = PROJECT_ROOT / "data" / "results"
LOGS_DIR: Path = PROJECT_ROOT / "logs"
STATE_DIR: Path = PROJECT_ROOT / "state"

@dataclass
class SocraticConfig:
    """
    Central configuration object for the Socratic Transformers pipeline.
    
    Attributes:
        generator_model_id (str): HuggingFace ID for the generator model.
        critic_model_id (str): HuggingFace ID for the critic model.
        seed (int): Global random seed.
        max_length (int): Maximum sequence length for generation.
        temperature (float): Sampling temperature for generation.
        do_sample (bool): Whether to use sampling.
        lora_r (int): LoRA rank.
        lora_alpha (float): LoRA alpha.
        lora_dropout (float): LoRA dropout.
        batch_size (int): Training batch size.
        gradient_accumulation_steps (int): Gradient accumulation steps.
        max_steps (int): Maximum training steps.
        learning_rate (float): Learning rate.
        weight_decay (float): Weight decay.
        warmup_ratio (float): Warmup ratio.
        logging_steps (int): Logging frequency.
        save_steps (int): Checkpoint saving frequency.
        output_dir (str): Output directory for checkpoints and logs.
    """
    generator_model_id: str = GENERATOR_MODEL_ID
    critic_model_id: str = CRITIC_MODEL_ID
    seed: int = DEFAULT_SEED
    max_length: int = 512
    temperature: float = 0.0
    do_sample: bool = False
    lora_r: int = 8
    lora_alpha: float = 16
    lora_dropout: float = 0.1
    batch_size: int = 2
    gradient_accumulation_steps: int = 4
    max_steps: int = 1000
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.03
    logging_steps: int = 50
    save_steps: int = 500
    output_dir: str = str(PROJECT_ROOT / "data" / "results" / "checkpoints")
    log_dir: str = str(LOGS_DIR)
    raw_data_dir: str = str(DATA_RAW_DIR)
    processed_data_dir: str = str(DATA_PROCESSED_DIR)
    results_dir: str = str(DATA_RESULTS_DIR)

    def __post_init__(self):
        """Ensure paths are Path objects and directories exist."""
        self.output_dir = Path(self.output_dir)
        self.log_dir = Path(self.log_dir)
        self.raw_data_dir = Path(self.raw_data_dir)
        self.processed_data_dir = Path(self.processed_data_dir)
        self.results_dir = Path(self.results_dir)
        
        # Ensure required directories exist
        for path in [self.output_dir, self.log_dir, self.raw_data_dir, 
                     self.processed_data_dir, self.results_dir]:
            path.mkdir(parents=True, exist_ok=True)

# Global configuration instance
_global_config: Optional[SocraticConfig] = None

def get_config() -> SocraticConfig:
    """
    Get the global configuration instance.
    
    Returns:
        SocraticConfig: The global configuration object.
    """
    global _global_config
    if _global_config is None:
        _global_config = SocraticConfig()
    return _global_config

def set_global_config(config: SocraticConfig) -> None:
    """
    Set the global configuration instance.
    
    Args:
        config (SocraticConfig): The configuration object to set.
    """
    global _global_config
    _global_config = config

def load_config_from_env() -> SocraticConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        SocraticConfig: Configuration object with values overridden by env vars.
    """
    config = SocraticConfig()
    
    # Override with environment variables if present
    if os.getenv("GENERATOR_MODEL_ID"):
        config.generator_model_id = os.getenv("GENERATOR_MODEL_ID")
    if os.getenv("CRITIC_MODEL_ID"):
        config.critic_model_id = os.getenv("CRITIC_MODEL_ID")
    if os.getenv("RANDOM_SEED"):
        config.seed = int(os.getenv("RANDOM_SEED"))
    if os.getenv("MAX_LENGTH"):
        config.max_length = int(os.getenv("MAX_LENGTH"))
    if os.getenv("TEMPERATURE"):
        config.temperature = float(os.getenv("TEMPERATURE"))
    if os.getenv("LORA_R"):
        config.lora_r = int(os.getenv("LORA_R"))
    if os.getenv("LORA_ALPHA"):
        config.lora_alpha = float(os.getenv("LORA_ALPHA"))
    if os.getenv("BATCH_SIZE"):
        config.batch_size = int(os.getenv("BATCH_SIZE"))
    if os.getenv("GRADIENT_ACCUMULATION_STEPS"):
        config.gradient_accumulation_steps = int(os.getenv("GRADIENT_ACCUMULATION_STEPS"))
    if os.getenv("MAX_STEPS"):
        config.max_steps = int(os.getenv("MAX_STEPS"))
    if os.getenv("LEARNING_RATE"):
        config.learning_rate = float(os.getenv("LEARNING_RATE"))
    if os.getenv("OUTPUT_DIR"):
        config.output_dir = Path(os.getenv("OUTPUT_DIR"))
    if os.getenv("LOG_DIR"):
        config.log_dir = Path(os.getenv("LOG_DIR"))
    if os.getenv("RAW_DATA_DIR"):
        config.raw_data_dir = Path(os.getenv("RAW_DATA_DIR"))
    if os.getenv("PROCESSED_DATA_DIR"):
        config.processed_data_dir = Path(os.getenv("PROCESSED_DATA_DIR"))
    if os.getenv("RESULTS_DIR"):
        config.results_dir = Path(os.getenv("RESULTS_DIR"))
        
    return config

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility across all libraries.
    
    Args:
        seed (int, optional): Seed value. Defaults to config seed.
    """
    if seed is None:
        seed = get_config().seed
        
    random.seed(seed)
    np.random.seed(seed)
    
    # Set torch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def init_project() -> None:
    """
    Initialize the project by setting up global configuration and directories.
    """
    global _global_config
    _global_config = load_config_from_env()
    set_seed(_global_config.seed)
    
    # Ensure all required directories exist
    for path in [_global_config.output_dir, _global_config.log_dir, 
                 _global_config.raw_data_dir, _global_config.processed_data_dir, 
                 _global_config.results_dir]:
        path.mkdir(parents=True, exist_ok=True)

def main():
    """
    Main entry point for configuration testing.
    """
    print("Initializing Socratic Transformers configuration...")
    init_project()
    config = get_config()
    
    print(f"Generator Model ID: {config.generator_model_id}")
    print(f"Critic Model ID: {config.critic_model_id}")
    print(f"Random Seed: {config.seed}")
    print(f"Output Directory: {config.output_dir}")
    print(f"Log Directory: {config.log_dir}")
    print(f"Raw Data Directory: {config.raw_data_dir}")
    print(f"Processed Data Directory: {config.processed_data_dir}")
    print(f"Results Directory: {config.results_dir}")
    
    # Verify directories exist
    assert config.output_dir.exists(), f"Output directory does not exist: {config.output_dir}"
    assert config.log_dir.exists(), f"Log directory does not exist: {config.log_dir}"
    assert config.raw_data_dir.exists(), f"Raw data directory does not exist: {config.raw_data_dir}"
    assert config.processed_data_dir.exists(), f"Processed data directory does not exist: {config.processed_data_dir}"
    assert config.results_dir.exists(), f"Results directory does not exist: {config.results_dir}"
    
    print("Configuration initialized successfully!")

if __name__ == "__main__":
    main()
