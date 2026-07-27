"""
Environment configuration management for the Socratic Transformers project.
Handles random seeds, model paths, and project directory structure.
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
    Central configuration class for the Socratic Transformers project.
    Encapsulates all hyperparameters, paths, and seed settings.
    """
    # Random Seeds
    seed: int = 42
    seed_list: List[int] = field(default_factory=lambda: [42, 123, 456, 789, 1011, 1213, 1415, 1617, 1819, 2021])

    # Model Paths
    base_model_path: str = "microsoft/phi-1.5"
    fallback_model_path: str = "microsoft/phi-1"
    tokenizer_path: Optional[str] = None

    # Data Paths
    data_root: str = "data"
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    results_dir: str = "data/results"
    logs_dir: str = "data/logs"

    # Training Hyperparameters
    max_seq_length: int = 2048
    batch_size: int = 1
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    num_train_epochs: float = 3.0
    weight_decay: float = 0.01
    warmup_ratio: float = 0.03

    # LoRA Parameters
    lora_r: int = 64
    lora_alpha: int = 128
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = field(
        default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"]
    )

    # Quantization
    use_4bit: bool = True
    use_8bit: bool = False

    # Evaluation
    eval_batch_size: int = 4
    prediction_error_threshold: float = 0.05
    ngram_overlap_threshold: float = 0.9

    # Timeouts & Limits
    training_timeout_hours: int = 6
    max_dialogue_turns: int = 5

    # Output Paths
    output_dir: str = "data/results"
    logging_dir: str = "data/logs"

    def __post_init__(self):
        """Ensure tokenizer defaults to base model if not specified."""
        if self.tokenizer_path is None:
            self.tokenizer_path = self.base_model_path

    def get_seed_list(self) -> List[int]:
        """Returns the list of seeds to use for the experiment sweep."""
        return self.seed_list

    def set_global_seed(self, seed: Optional[int] = None):
        """Sets the global random seed for reproducibility."""
        if seed is None:
            seed = self.seed
        random.seed(seed)
        np.random.seed(seed)
        os.environ["PYTHONHASHSEED"] = str(seed)
        # Note: torch.cuda.manual_seed is handled in model_loader.py when torch is available


# Global config instance (lazy initialization)
_global_config: Optional[SocraticConfig] = None


def load_config_from_env() -> SocraticConfig:
    """
    Loads configuration from environment variables, falling back to defaults.
    """
    config_dict = {}

    # Seeds
    if os.getenv("SOCRATIC_SEED"):
        config_dict["seed"] = int(os.getenv("SOCRATIC_SEED"))

    # Paths
    if os.getenv("SOCRATIC_BASE_MODEL"):
        config_dict["base_model_path"] = os.getenv("SOCRATIC_BASE_MODEL")
    if os.getenv("SOCRATIC_DATA_ROOT"):
        config_dict["data_root"] = os.getenv("SOCRATIC_DATA_ROOT")

    # Training
    if os.getenv("SOCRATIC_BATCH_SIZE"):
        config_dict["batch_size"] = int(os.getenv("SOCRATIC_BATCH_SIZE"))
    if os.getenv("SOCRATIC_LR"):
        config_dict["learning_rate"] = float(os.getenv("SOCRATIC_LR"))
    if os.getenv("SOCRATIC_EPOCHS"):
        config_dict["num_train_epochs"] = float(os.getenv("SOCRATIC_EPOCHS"))

    # LoRA
    if os.getenv("SOCRATIC_LORA_R"):
        config_dict["lora_r"] = int(os.getenv("SOCRATIC_LORA_R"))
    if os.getenv("SOCRATIC_LORA_ALPHA"):
        config_dict["lora_alpha"] = int(os.getenv("SOCRATIC_LORA_ALPHA"))

    return SocraticConfig(**config_dict)


def get_config() -> SocraticConfig:
    """
    Returns the global configuration instance, initializing it if necessary.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
    return _global_config


def set_global_config(config: SocraticConfig):
    """
    Explicitly sets the global configuration instance.
    """
    global _global_config
    _global_config = config


def ensure_directories(config: Optional[SocraticConfig] = None):
    """
    Creates all necessary directories defined in the configuration.
    """
    if config is None:
        config = get_config()

    dirs = [
        config.data_root,
        config.raw_data_dir,
        config.processed_data_dir,
        config.results_dir,
        config.logs_dir,
        config.output_dir,
    ]

    for dir_path in dirs:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)


def init_project():
    """
    Initializes the project by loading config and creating directories.
    Should be called at the entry point of scripts.
    """
    config = load_config_from_env()
    set_global_config(config)
    ensure_directories(config)
    config.set_global_seed(config.seed)
    return config


def merge_configs(base: SocraticConfig, overrides: Dict[str, Any]) -> SocraticConfig:
    """
    Merges a dictionary of overrides into a base configuration.
    """
    import copy
    new_dict = copy.deepcopy(base.__dict__)
    new_dict.update(overrides)
    return SocraticConfig(**new_dict)
