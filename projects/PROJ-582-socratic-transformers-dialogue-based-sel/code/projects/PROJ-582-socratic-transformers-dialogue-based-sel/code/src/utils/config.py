"""
Environment configuration management for Socratic Transformers project.

Handles random seeds, model paths, and project directory structure initialization.
Ensures reproducibility and consistent environment setup across runs.
"""
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np

# Default paths relative to project root
DEFAULT_PROJECT_ROOT = "projects/PROJ-582-socratic-transformers-dialogue-based-sel/code"
DEFAULT_DATA_DIR = "data"
DEFAULT_RAW_DATA_DIR = "data/raw"
DEFAULT_PROCESSED_DATA_DIR = "data/processed"
DEFAULT_RESULTS_DIR = "data/results"
DEFAULT_LOGS_DIR = "logs"
DEFAULT_MODELS_DIR = "models"
DEFAULT_CHECKPOINTS_DIR = "checkpoints"

# Default model paths
DEFAULT_BASE_MODEL = "meta-llama/Llama-2-7b-hf"
DEFAULT_CRITIC_MODEL = "meta-llama/Llama-2-7b-hf"
DEFAULT_TOKENIZER = "meta-llama/Llama-2-7b-hf"

# Default random seed for reproducibility
DEFAULT_SEED = 42


@dataclass
class SocraticConfig:
    """
    Configuration container for the Socratic Transformers project.
    
    Attributes:
        project_root: Root directory of the project
        data_dir: Base directory for all data
        raw_data_dir: Directory for raw, unprocessed datasets
        processed_data_dir: Directory for processed datasets
        results_dir: Directory for experimental results and metrics
        logs_dir: Directory for log files
        models_dir: Directory for downloaded/loaded models
        checkpoints_dir: Directory for training checkpoints
        
        base_model_path: Path/hub_id for the base model to train
        critic_model_path: Path/hub_id for the frozen critic model
        tokenizer_path: Path/hub_id for the tokenizer
        
        seed: Random seed for reproducibility
        device: Device to run models on (cpu, cuda, mps)
        max_length: Maximum sequence length for generation
        batch_size: Training batch size
        learning_rate: Learning rate for optimization
        num_epochs: Number of training epochs
        use_lora: Whether to use LoRA for fine-tuning
        lora_r: LoRA rank
        lora_alpha: LoRA alpha scaling
        lora_dropout: LoRA dropout rate
        
        max_tokens: Maximum tokens for generation
        temperature: Sampling temperature
        top_p: Nucleus sampling parameter
        do_sample: Whether to use sampling
        
        timeout_seconds: Maximum training time in seconds
        oom_exit_code: Exit code for OOM detection
    """
    # Project structure
    project_root: str = DEFAULT_PROJECT_ROOT
    data_dir: str = DEFAULT_DATA_DIR
    raw_data_dir: str = DEFAULT_RAW_DATA_DIR
    processed_data_dir: str = DEFAULT_PROCESSED_DATA_DIR
    results_dir: str = DEFAULT_RESULTS_DIR
    logs_dir: str = DEFAULT_LOGS_DIR
    models_dir: str = DEFAULT_MODELS_DIR
    checkpoints_dir: str = DEFAULT_CHECKPOINTS_DIR
    
    # Model paths
    base_model_path: str = os.getenv("BASE_MODEL_PATH", DEFAULT_BASE_MODEL)
    critic_model_path: str = os.getenv("CRITIC_MODEL_PATH", DEFAULT_CRITIC_MODEL)
    tokenizer_path: str = os.getenv("TOKENIZER_PATH", DEFAULT_TOKENIZER)
    
    # Reproducibility
    seed: int = int(os.getenv("SEED", DEFAULT_SEED))
    
    # Hardware
    device: str = os.getenv("DEVICE", "cpu")
    
    # Training parameters
    max_length: int = int(os.getenv("MAX_LENGTH", "512"))
    batch_size: int = int(os.getenv("BATCH_SIZE", "2"))
    learning_rate: float = float(os.getenv("LEARNING_RATE", "1e-4"))
    num_epochs: int = int(os.getenv("NUM_EPOCHS", "3"))
    use_lora: bool = os.getenv("USE_LORA", "true").lower() == "true"
    lora_r: int = int(os.getenv("LORA_R", "8"))
    lora_alpha: int = int(os.getenv("LORA_ALPHA", "16"))
    lora_dropout: float = float(os.getenv("LORA_DROPOUT", "0.1"))
    
    # Generation parameters
    max_tokens: int = int(os.getenv("MAX_TOKENS", "256"))
    temperature: float = float(os.getenv("TEMPERATURE", "0.7"))
    top_p: float = float(os.getenv("TOP_P", "0.9"))
    do_sample: bool = os.getenv("DO_SAMPLE", "true").lower() == "true"
    
    # Execution constraints
    timeout_seconds: int = int(os.getenv("TIMEOUT_SECONDS", "3600"))
    oom_exit_code: int = int(os.getenv("OOM_EXIT_CODE", "137"))

    def __post_init__(self):
        """Validate and normalize paths."""
        self.project_root = Path(self.project_root)
        self.data_dir = self.project_root / self.data_dir
        self.raw_data_dir = self.data_dir / "raw"
        self.processed_data_dir = self.data_dir / "processed"
        self.results_dir = self.data_dir / "results"
        self.logs_dir = self.project_root / self.logs_dir
        self.models_dir = self.project_root / self.models_dir
        self.checkpoints_dir = self.project_root / self.checkpoints_dir

        # Convert back to strings for compatibility if needed
        self.project_root = str(self.project_root)
        self.data_dir = str(self.data_dir)
        self.raw_data_dir = str(self.raw_data_dir)
        self.processed_data_dir = str(self.processed_data_dir)
        self.results_dir = str(self.results_dir)
        self.logs_dir = str(self.logs_dir)
        self.models_dir = str(self.models_dir)
        self.checkpoints_dir = str(self.checkpoints_dir)


# Global config instance (singleton pattern)
_global_config: Optional[SocraticConfig] = None


def load_config_from_env() -> SocraticConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        SocraticConfig instance populated with environment variables.
    """
    return SocraticConfig()


def get_config() -> SocraticConfig:
    """
    Get the global configuration instance.
    
    Creates a new instance if none exists.
    
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


def ensure_directories(config: Optional[SocraticConfig] = None) -> None:
    """
    Ensure all required directories exist.
    
    Args:
        config: Optional config instance. If None, uses global config.
    """
    if config is None:
        config = get_config()
    
    directories = [
        config.project_root,
        config.data_dir,
        config.raw_data_dir,
        config.processed_data_dir,
        config.results_dir,
        config.logs_dir,
        config.models_dir,
        config.checkpoints_dir,
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def init_project() -> SocraticConfig:
    """
    Initialize the project environment.
    
    This function:
    1. Loads configuration from environment variables
    2. Sets it as the global config
    3. Ensures all required directories exist
    4. Sets random seeds for reproducibility
    
    Returns:
        Initialized SocraticConfig instance.
    """
    config = load_config_from_env()
    set_global_config(config)
    ensure_directories(config)
    set_seed(config.seed)
    return config


def set_seed(seed: int) -> None:
    """
    Set random seeds for reproducibility.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    if torch := None:  # Avoid import if not available
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        except ImportError:
            pass


def merge_configs(base: SocraticConfig, overrides: Dict[str, Any]) -> SocraticConfig:
    """
    Merge a base config with override values.
    
    Args:
        base: Base SocraticConfig instance.
        overrides: Dictionary of key-value pairs to override.
    
    Returns:
        New SocraticConfig instance with merged values.
    """
    import dataclasses
    
    base_dict = dataclasses.asdict(base)
    base_dict.update(overrides)
    return SocraticConfig(**base_dict)


# Initialize project on module import if explicitly requested
if os.getenv("INIT_PROJECT_ON_IMPORT", "false").lower() == "true":
    init_project()
