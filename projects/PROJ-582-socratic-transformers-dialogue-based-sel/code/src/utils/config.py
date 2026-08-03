"""
Environment configuration management for random seeds and model paths.

This module provides the SocraticConfig dataclass and utility functions to
manage project-wide configuration, including random seed initialization
for reproducibility across numpy, torch, and python random modules.
"""
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np

# Default paths relative to project root
DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_DATA_DIR = DEFAULT_PROJECT_ROOT / "data"
DEFAULT_RESULTS_DIR = DEFAULT_DATA_DIR / "results"
DEFAULT_LOGS_DIR = DEFAULT_DATA_DIR / "logs"

@dataclass
class SocraticConfig:
    """
    Central configuration container for the Socratic Transformers project.

    Attributes:
        project_root: Root directory of the project.
        data_dir: Base directory for data storage.
        results_dir: Directory for output metrics and results.
        logs_dir: Directory for log files.
        seed: Random seed for reproducibility.
        model_name: HuggingFace model identifier for the base model.
        critic_model_name: HuggingFace model identifier for the frozen critic.
        output_dir: Directory for generation outputs.
        max_seq_length: Maximum sequence length for tokenization.
        batch_size: Training/inference batch size.
        device: Device to run models on ('cpu', 'cuda', 'mps').
        use_4bit: Enable 4-bit quantization for memory efficiency.
        lora_rank: Rank for LoRA adaptation.
        lora_alpha: Alpha scaling for LoRA.
        lora_dropout: Dropout for LoRA layers.
        target_modules: List of module names to apply LoRA to.
        num_train_epochs: Number of training epochs.
        learning_rate: Optimizer learning rate.
        weight_decay: Optimizer weight decay.
        warmup_steps: Number of warmup steps.
        logging_steps: Frequency of logging.
        save_steps: Frequency of saving checkpoints.
        eval_steps: Frequency of evaluation.
        max_grad_norm: Maximum gradient norm for clipping.
        gradient_accumulation_steps: Steps for gradient accumulation.
    """
    project_root: Path = field(default_factory=lambda: DEFAULT_PROJECT_ROOT)
    data_dir: Path = field(default_factory=lambda: DEFAULT_DATA_DIR)
    results_dir: Path = field(default_factory=lambda: DEFAULT_RESULTS_DIR)
    logs_dir: Path = field(default_factory=lambda: DEFAULT_LOGS_DIR)
    
    # Randomness
    seed: int = 42
    
    # Model paths
    model_name: str = "meta-llama/Llama-3.2-1B"
    critic_model_name: str = "meta-llama/Llama-3.2-1B"
    output_dir: Path = field(default_factory=lambda: DEFAULT_PROJECT_ROOT / "data" / "results" / "dialogues")
    
    # Hyperparameters
    max_seq_length: int = 2048
    batch_size: int = 2
    device: str = "cpu"
    use_4bit: bool = True
    
    # LoRA parameters
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    target_modules: List[str] = field(default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"])
    
    # Training parameters
    num_train_epochs: int = 3
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_steps: int = 50
    logging_steps: int = 10
    save_steps: int = 100
    eval_steps: int = 100
    max_grad_norm: float = 1.0
    gradient_accumulation_steps: int = 4

    def __post_init__(self):
        """Ensure paths are Path objects and resolve relative paths."""
        if isinstance(self.project_root, str):
            self.project_root = Path(self.project_root)
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
        if isinstance(self.results_dir, str):
            self.results_dir = Path(self.results_dir)
        if isinstance(self.logs_dir, str):
            self.logs_dir = Path(self.logs_dir)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)

        # Resolve relative paths against project root if not absolute
        if not self.project_root.is_absolute():
            self.project_root = self.project_root.resolve()
        
        # Ensure data subdirectories are relative to data_dir if not absolute
        if not self.data_dir.is_absolute():
            self.data_dir = self.project_root / self.data_dir
        
        if not self.results_dir.is_absolute():
            self.results_dir = self.data_dir / self.results_dir.relative_to(self.data_dir) if self.results_dir.is_relative_to(self.data_dir) else self.data_dir / self.results_dir
        
        if not self.logs_dir.is_absolute():
            self.logs_dir = self.data_dir / self.logs_dir.relative_to(self.data_dir) if self.logs_dir.is_relative_to(self.data_dir) else self.data_dir / self.logs_dir

        if not self.output_dir.is_absolute():
            self.output_dir = self.data_dir / self.output_dir.relative_to(self.data_dir) if self.output_dir.is_relative_to(self.data_dir) else self.data_dir / self.output_dir

# Global config instance (lazy initialization)
_global_config: Optional[SocraticConfig] = None

def load_config_from_env() -> SocraticConfig:
    """
    Load configuration from environment variables, falling back to defaults.
    
    Returns:
        SocraticConfig instance populated from environment or defaults.
    """
    env_vars = {
        "PROJECT_ROOT": "DEFAULT_PROJECT_ROOT",
        "DATA_DIR": "DEFAULT_DATA_DIR",
        "SEED": "42",
        "MODEL_NAME": "meta-llama/Llama-3.2-1B",
        "CRITIC_MODEL_NAME": "meta-llama/Llama-3.2-1B",
        "MAX_SEQ_LENGTH": "2048",
        "BATCH_SIZE": "2",
        "DEVICE": "cpu",
        "USE_4BIT": "True",
        "LORA_RANK": "8",
        "LORA_ALPHA": "16",
        "LORA_DROPOUT": "0.05",
        "NUM_TRAIN_EPOCHS": "3",
        "LEARNING_RATE": "2e-4",
        "WEIGHT_DECAY": "0.01",
        "WARMUP_STEPS": "50",
        "LOGGING_STEPS": "10",
        "SAVE_STEPS": "100",
        "EVAL_STEPS": "100",
        "MAX_GRAD_NORM": "1.0",
        "GRADIENT_ACCUMULATION_STEPS": "4",
    }

    config_kwargs = {}
    
    # Handle path-specific overrides
    if os.getenv("PROJECT_ROOT"):
        config_kwargs["project_root"] = Path(os.getenv("PROJECT_ROOT"))
    if os.getenv("DATA_DIR"):
        config_kwargs["data_dir"] = Path(os.getenv("DATA_DIR"))

    # Handle simple value overrides
    seed_val = os.getenv("SEED")
    if seed_val:
        config_kwargs["seed"] = int(seed_val)
    
    model_name = os.getenv("MODEL_NAME")
    if model_name:
        config_kwargs["model_name"] = model_name
    
    critic_model_name = os.getenv("CRITIC_MODEL_NAME")
    if critic_model_name:
        config_kwargs["critic_model_name"] = critic_model_name
    
    max_seq = os.getenv("MAX_SEQ_LENGTH")
    if max_seq:
        config_kwargs["max_seq_length"] = int(max_seq)
    
    batch_size = os.getenv("BATCH_SIZE")
    if batch_size:
        config_kwargs["batch_size"] = int(batch_size)
    
    device = os.getenv("DEVICE")
    if device:
        config_kwargs["device"] = device
    
    use_4bit = os.getenv("USE_4BIT")
    if use_4bit:
        config_kwargs["use_4bit"] = use_4bit.lower() in ("true", "1", "yes")
    
    lora_rank = os.getenv("LORA_RANK")
    if lora_rank:
        config_kwargs["lora_rank"] = int(lora_rank)
    
    lora_alpha = os.getenv("LORA_ALPHA")
    if lora_alpha:
        config_kwargs["lora_alpha"] = int(lora_alpha)
    
    lora_dropout = os.getenv("LORA_DROPOUT")
    if lora_dropout:
        config_kwargs["lora_dropout"] = float(lora_dropout)
    
    num_epochs = os.getenv("NUM_TRAIN_EPOCHS")
    if num_epochs:
        config_kwargs["num_train_epochs"] = int(num_epochs)
    
    lr = os.getenv("LEARNING_RATE")
    if lr:
        config_kwargs["learning_rate"] = float(lr)
    
    wd = os.getenv("WEIGHT_DECAY")
    if wd:
        config_kwargs["weight_decay"] = float(wd)
    
    warmup = os.getenv("WARMUP_STEPS")
    if warmup:
        config_kwargs["warmup_steps"] = int(warmup)
    
    log_steps = os.getenv("LOGGING_STEPS")
    if log_steps:
        config_kwargs["logging_steps"] = int(log_steps)
    
    save_steps = os.getenv("SAVE_STEPS")
    if save_steps:
        config_kwargs["save_steps"] = int(save_steps)
    
    eval_steps = os.getenv("EVAL_STEPS")
    if eval_steps:
        config_kwargs["eval_steps"] = int(eval_steps)
    
    max_grad = os.getenv("MAX_GRAD_NORM")
    if max_grad:
        config_kwargs["max_grad_norm"] = float(max_grad)
    
    grad_acc = os.getenv("GRADIENT_ACCUMULATION_STEPS")
    if grad_acc:
        config_kwargs["gradient_accumulation_steps"] = int(grad_acc)

    return SocraticConfig(**config_kwargs)

def get_config() -> SocraticConfig:
    """
    Get the global configuration instance, initializing it if necessary.
    
    Returns:
        The global SocraticConfig instance.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
        ensure_directories(_global_config)
    return _global_config

def set_global_config(config: SocraticConfig) -> None:
    """
    Set the global configuration instance explicitly.
    
    Args:
        config: The SocraticConfig instance to set as global.
    """
    global _global_config
    _global_config = config
    ensure_directories(config)

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility across all relevant libraries.
    
    Args:
        seed: The seed value. If None, uses the seed from the global config.
    """
    if seed is None:
        config = get_config()
        seed = config.seed
    
    random.seed(seed)
    np.random.seed(seed)
    
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # Torch might not be installed in all environments

def ensure_directories(config: Optional[SocraticConfig] = None) -> None:
    """
    Ensure all required directories exist based on the configuration.
    
    Args:
        config: Optional config instance. If None, uses the global config.
    """
    if config is None:
        config = get_config()
    
    directories = [
        config.data_dir,
        config.data_dir / "raw",
        config.data_dir / "processed",
        config.data_dir / "results",
        config.logs_dir,
        config.output_dir,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def init_project() -> None:
    """
    Initialize the project by loading config and ensuring directories exist.
    This is typically called at the entry point of scripts.
    """
    config = get_config()
    ensure_directories(config)
    set_seed()

def merge_configs(base: SocraticConfig, overrides: Dict[str, Any]) -> SocraticConfig:
    """
    Create a new config by merging base config with override values.
    
    Args:
        base: The base SocraticConfig instance.
        overrides: Dictionary of attribute names to override values.
        
    Returns:
        A new SocraticConfig instance with overrides applied.
    """
    import copy
    new_config = copy.deepcopy(base)
    for key, value in overrides.items():
        if hasattr(new_config, key):
            setattr(new_config, key, value)
        else:
            raise ValueError(f"Unknown config attribute: {key}")
    return new_config

# Convenience function for scripts that need immediate setup
def setup_environment() -> SocraticConfig:
    """
    Full environment setup: load config, ensure dirs, set seeds.
    
    Returns:
        The configured SocraticConfig instance.
    """
    init_project()
    return get_config()
