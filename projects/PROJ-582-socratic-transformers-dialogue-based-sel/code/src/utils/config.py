"""
Configuration management for Socratic Transformers project.

Handles random seeds, model paths, and data directory structures.
"""
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np

@dataclass
class SocraticConfig:
    """Main configuration class for the Socratic Transformers project."""

    # Randomness control
    seed: int = 42
    deterministic: bool = True

    # Model paths
    base_model_name: str = "meta-llama/Llama-2-7b-hf"
    critic_model_name: str = "meta-llama/Llama-2-7b-hf"  # Default to base if no specific critic

    # Data directories (relative to project root)
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[3])
    data_raw_dir: Path = field(init=False)
    data_processed_dir: Path = field(init=False)
    data_results_dir: Path = field(init=False)
    state_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)

    # Training parameters
    max_seq_length: int = 2048
    batch_size: int = 1
    gradient_accumulation_steps: int = 4
    learning_rate: float = 2e-4
    num_train_epochs: int = 3
    weight_decay: float = 0.01
    warmup_steps: int = 50

    # LoRA parameters
    lora_r: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    lora_target_modules: List[str] = field(default_factory=lambda: ["q_proj", "v_proj"])

    # Evaluation
    eval_batch_size: int = 4
    eval_max_samples: Optional[int] = None  # None = use all

    def __post_init__(self):
        """Initialize derived paths after dataclass init."""
        self.data_raw_dir = self.project_root / "data" / "raw"
        self.data_processed_dir = self.project_root / "data" / "processed"
        self.data_results_dir = self.project_root / "data" / "results"
        self.state_dir = self.project_root / "state"
        self.logs_dir = self.project_root / "logs"

    def set_seed(self):
        """Set global random seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        try:
            import torch
            torch.manual_seed(self.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self.seed)
        except ImportError:
            pass

_global_config: Optional[SocraticConfig] = None

def get_config() -> SocraticConfig:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = SocraticConfig()
    return _global_config

def set_global_config(config: SocraticConfig) -> None:
    """Set the global configuration instance."""
    global _global_config
    _global_config = config

def load_config_from_env() -> SocraticConfig:
    """Load configuration from environment variables."""
    config = SocraticConfig()

    if "SOCRATIC_SEED" in os.environ:
        config.seed = int(os.environ["SOCRATIC_SEED"])

    if "SOCRATIC_BASE_MODEL" in os.environ:
        config.base_model_name = os.environ["SOCRATIC_BASE_MODEL"]

    if "SOCRATIC_CRITIC_MODEL" in os.environ:
        config.critic_model_name = os.environ["SOCRATIC_CRITIC_MODEL"]

    if "SOCRATIC_PROJECT_ROOT" in os.environ:
        config.project_root = Path(os.environ["SOCRATIC_PROJECT_ROOT"])
        # Re-initialize paths
        config.__post_init__()

    return config

def init_project() -> None:
    """Initialize project directories and global config."""
    config = get_config()
    config.set_seed()

    # Create directories
    dirs = [
        config.data_raw_dir,
        config.data_processed_dir,
        config.data_results_dir,
        config.state_dir,
        config.logs_dir
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
