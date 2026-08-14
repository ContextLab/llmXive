import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List
import numpy as np

@dataclass
class SocraticConfig:
    """Central configuration for the Socratic Transformers project."""
    
    # Model IDs
    BASE_MODEL_ID: str = "meta-llama/Llama-2-7b-hf"
    CRITIC_MODEL_ID: str = "microsoft/Phi-3-mini-4k-instruct"
    
    # Paths
    QUESTION_BANK_PATH: str = "data/processed/question_bank.jsonl"
    DATA_DIR: str = "data"
    RAW_DATA_DIR: str = "data/raw"
    PROCESSED_DATA_DIR: str = "data/processed"
    RESULTS_DIR: str = "data/results"
    STATE_DIR: str = "state"
    
    # Training parameters
    MAX_LENGTH: int = 2048
    BATCH_SIZE: int = 2
    GRADIENT_ACCUMULATION_STEPS: int = 4
    LEARNING_RATE: float = 2e-4
    NUM_EPOCHS: int = 3
    MAX_STEPS: Optional[int] = None
    
    # Quantization
    USE_4BIT: bool = True
    USE_8BIT: bool = False
    
    # Random seeds
    SEED: int = 42
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    # Evaluation
    EVAL_BATCH_SIZE: int = 4
    EVAL_MAX_SAMPLES: Optional[int] = None
    
    # Ablation
    ABLATON_TOKEN_TOLERANCE: int = 1
    
    def __post_init__(self):
        """Ensure paths are Path objects."""
        self.DATA_DIR = Path(self.DATA_DIR)
        self.RAW_DATA_DIR = Path(self.RAW_DATA_DIR)
        self.PROCESSED_DATA_DIR = Path(self.PROCESSED_DATA_DIR)
        self.RESULTS_DIR = Path(self.RESULTS_DIR)
        self.STATE_DIR = Path(self.STATE_DIR)
        
        # Set random seeds
        set_seed(self.SEED)

_global_config: Optional[SocraticConfig] = None

def get_config() -> SocraticConfig:
    """Return the global configuration, initializing if necessary."""
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
    return _global_config

def set_global_config(config: SocraticConfig) -> None:
    """Set the global configuration explicitly."""
    global _global_config
    _global_config = config

def load_config_from_env() -> SocraticConfig:
    """Load configuration from environment variables with defaults."""
    config = SocraticConfig(
        BASE_MODEL_ID=os.getenv("BASE_MODEL_ID", "meta-llama/Llama-2-7b-hf"),
        CRITIC_MODEL_ID=os.getenv("CRITIC_MODEL_ID", "microsoft/Phi-3-mini-4k-instruct"),
        QUESTION_BANK_PATH=os.getenv("QUESTION_BANK_PATH", "data/processed/question_bank.jsonl"),
        MAX_LENGTH=int(os.getenv("MAX_LENGTH", "2048")),
        BATCH_SIZE=int(os.getenv("BATCH_SIZE", "2")),
        GRADIENT_ACCUMULATION_STEPS=int(os.getenv("GRADIENT_ACCUMULATION_STEPS", "4")),
        LEARNING_RATE=float(os.getenv("LEARNING_RATE", "2e-4")),
        NUM_EPOCHS=int(os.getenv("NUM_EPOCHS", "3")),
        MAX_STEPS=int(os.getenv("MAX_STEPS", "-1")) if os.getenv("MAX_STEPS") else None,
        USE_4BIT=os.getenv("USE_4BIT", "true").lower() == "true",
        USE_8BIT=os.getenv("USE_8BIT", "false").lower() == "true",
        SEED=int(os.getenv("SEED", "42")),
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
        LOG_FILE=os.getenv("LOG_FILE"),
        EVAL_BATCH_SIZE=int(os.getenv("EVAL_BATCH_SIZE", "4")),
        EVAL_MAX_SAMPLES=int(os.getenv("EVAL_MAX_SAMPLES", "-1")) if os.getenv("EVAL_MAX_SAMPLES") else None,
    )
    return config

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
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
    """Initialize project directories based on config."""
    config = get_config()
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)

def main():
    """Entry point for config module."""
    config = get_config()
    print(f"Configuration loaded:")
    print(f"  Base Model: {config.BASE_MODEL_ID}")
    print(f"  Critic Model: {config.CRICIT_MODEL_ID}")
    print(f"  Seed: {config.SEED}")

if __name__ == "__main__":
    main()
