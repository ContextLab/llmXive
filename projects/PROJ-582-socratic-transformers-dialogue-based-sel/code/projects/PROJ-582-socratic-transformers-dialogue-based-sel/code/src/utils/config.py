"""
Environment configuration management for the Socratic Transformers project.

Handles random seeds, model paths, and project directories to ensure
reproducibility and consistent environment setup across runs.
"""
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List

import numpy as np

# Default paths relative to project root
DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_DATA_ROOT = DEFAULT_PROJECT_ROOT / "data"
DEFAULT_RESULTS_ROOT = DEFAULT_PROJECT_ROOT / "data" / "results"

# Model paths (can be overridden by environment variables)
DEFAULT_BASE_MODEL = "microsoft/phi-1.5"
DEFAULT_FALLBACK_MODEL = "microsoft/phi-1"
DEFAULT_LORA_TARGET_MODULES = ["q_proj", "v_proj", "k_proj", "o_proj"]

@dataclass
class SocraticConfig:
    """
    Central configuration container for the Socratic Transformers project.
    
    Attributes:
        project_root: Root directory of the project.
        data_root: Root directory for data storage.
        results_root: Directory for experiment results and logs.
        seed: Random seed for reproducibility.
        base_model: Path/hub ID for the base model.
        fallback_model: Path/hub ID for the OOM fallback model.
        lora_target_modules: Modules to target for LoRA adaptation.
        max_dialogue_turns: Maximum turns in a socratic dialogue.
        ngram_threshold: Threshold for detecting degenerate dialogues.
        debug: Enable debug mode with extra logging.
        _initialized: Flag to track if global state has been set.
    """
    project_root: Path = field(default_factory=lambda: DEFAULT_PROJECT_ROOT)
    data_root: Path = field(default_factory=lambda: DEFAULT_DATA_ROOT)
    results_root: Path = field(default_factory=lambda: DEFAULT_RESULTS_ROOT)
    
    seed: int = 42
    base_model: str = DEFAULT_BASE_MODEL
    fallback_model: str = DEFAULT_FALLBACK_MODEL
    lora_target_modules: List[str] = field(default_factory=lambda: DEFAULT_LORA_TARGET_MODULES)
    
    max_dialogue_turns: int = 5
    ngram_threshold: float = 0.9
    
    debug: bool = False
    
    _initialized: bool = field(default=False, repr=False, compare=False)

    def __post_init__(self):
        """Validate and normalize paths after initialization."""
        if isinstance(self.project_root, str):
            self.project_root = Path(self.project_root)
        if isinstance(self.data_root, str):
            self.data_root = Path(self.data_root)
        if isinstance(self.results_root, str):
            self.results_root = Path(self.results_root)
        
        # Ensure paths are absolute
        if not self.project_root.is_absolute():
            self.project_root = self.project_root.resolve()
        if not self.data_root.is_absolute():
            self.data_root = self.data_root.resolve()
        if not self.results_root.is_absolute():
            self.results_root = self.results_root.resolve()

    def set_seed(self):
        """Set random seeds for reproducibility across libraries."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        try:
            import torch
            torch.manual_seed(self.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self.seed)
        except ImportError:
            pass  # PyTorch might not be installed in all contexts

    def get_dataset_cache_dir(self) -> Path:
        """Return the cache directory for downloaded datasets."""
        return self.data_root / "cache"

    def get_processed_data_dir(self) -> Path:
        """Return the directory for processed datasets."""
        return self.data_root / "processed"

    def ensure_directories(self) -> None:
        """Create all necessary project directories if they don't exist."""
        dirs = [
            self.project_root,
            self.data_root,
            self.results_root,
            self.get_dataset_cache_dir(),
            self.get_processed_data_dir(),
            self.data_root / "raw",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

# Global configuration instance (lazy initialization)
_global_config: Optional[SocraticConfig] = None

def load_config_from_env() -> SocraticConfig:
    """
    Load configuration from environment variables.
    
    Environment variables:
        SOCRATIC_PROJECT_ROOT: Project root directory
        SOCRATIC_DATA_ROOT: Data root directory
        SOCRATIC_SEED: Random seed (integer)
        SOCRATIC_BASE_MODEL: Base model path
        SOCRATIC_FALLBACK_MODEL: Fallback model path
        SOCRATIC_MAX_DIALOGUE_TURNS: Max turns in dialogue
        SOCRATIC_NGRAM_THRESHOLD: Degenerate dialogue threshold
        SOCRATIC_DEBUG: Enable debug mode ("1", "true", "yes")
    
    Returns:
        SocraticConfig instance populated with environment values.
    """
    config = SocraticConfig()
    
    if os.getenv("SOCRATIC_PROJECT_ROOT"):
        config.project_root = Path(os.getenv("SOCRATIC_PROJECT_ROOT"))
    if os.getenv("SOCRATIC_DATA_ROOT"):
        config.data_root = Path(os.getenv("SOCRATIC_DATA_ROOT"))
    if os.getenv("SOCRATIC_RESULTS_ROOT"):
        config.results_root = Path(os.getenv("SOCRATIC_RESULTS_ROOT"))
    
    if os.getenv("SOCRATIC_SEED"):
        try:
            config.seed = int(os.getenv("SOCRATIC_SEED"))
        except ValueError:
            pass  # Keep default if invalid
    
    if os.getenv("SOCRATIC_BASE_MODEL"):
        config.base_model = os.getenv("SOCRATIC_BASE_MODEL")
    if os.getenv("SOCRATIC_FALLBACK_MODEL"):
        config.fallback_model = os.getenv("SOCRATIC_FALLBACK_MODEL")
    
    if os.getenv("SOCRATIC_MAX_DIALOGUE_TURNS"):
        try:
            config.max_dialogue_turns = int(os.getenv("SOCRATIC_MAX_DIALOGUE_TURNS"))
        except ValueError:
            pass
    
    if os.getenv("SOCRATIC_NGRAM_THRESHOLD"):
        try:
            config.ngram_threshold = float(os.getenv("SOCRATIC_NGRAM_THRESHOLD"))
        except ValueError:
            pass
    
    debug_val = os.getenv("SOCRATIC_DEBUG", "").lower()
    config.debug = debug_val in ("1", "true", "yes")
    
    return config

def get_config() -> SocraticConfig:
    """
    Get the global configuration instance.
    
    If no global config exists, loads from environment variables.
    
    Returns:
        The global SocraticConfig instance.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
        _global_config._initialized = True
    return _global_config

def set_global_config(config: SocraticConfig) -> None:
    """
    Set the global configuration instance explicitly.
    
    Args:
        config: The SocraticConfig instance to set as global.
    """
    global _global_config
    _global_config = config
    _global_config._initialized = True

def ensure_directories() -> None:
    """Ensure all required project directories exist."""
    config = get_config()
    config.ensure_directories()

def init_project() -> None:
    """
    Initialize the project environment.
    
    This function:
    1. Loads configuration from environment.
    2. Sets random seeds.
    3. Creates necessary directories.
    """
    config = load_config_from_env()
    set_global_config(config)
    config.set_seed()
    config.ensure_directories()

# Utility for merging configs
def merge_configs(base: SocraticConfig, overrides: Dict[str, Any]) -> SocraticConfig:
    """
    Create a new config by merging base with overrides.
    
    Args:
        base: Base configuration.
        overrides: Dictionary of fields to override.
    
    Returns:
        New SocraticConfig instance with merged values.
    """
    config_dict = {
        "project_root": base.project_root,
        "data_root": base.data_root,
        "results_root": base.results_root,
        "seed": base.seed,
        "base_model": base.base_model,
        "fallback_model": base.fallback_model,
        "lora_target_modules": base.lora_target_modules,
        "max_dialogue_turns": base.max_dialogue_turns,
        "ngram_threshold": base.ngram_threshold,
        "debug": base.debug,
    }
    config_dict.update(overrides)
    return SocraticConfig(**config_dict)
