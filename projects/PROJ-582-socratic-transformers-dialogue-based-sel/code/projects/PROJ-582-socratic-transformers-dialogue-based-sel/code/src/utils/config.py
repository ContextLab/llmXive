"""
Environment configuration management for the Socratic Transformers project.
Handles random seeds, model paths, and training hyperparameters via environment variables.
"""
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np

@dataclass
class SocraticConfig:
    """
    Central configuration dataclass for the Socratic Transformers pipeline.
    Populates values from environment variables with sensible defaults.
    """
    # Random Seeds for reproducibility
    seed: int = 42
    torch_seed: int = 42
    numpy_seed: int = 42
    python_seed: int = 42

    # Model Paths
    base_model_path: str = "microsoft/phi-1.5"
    fallback_model_path: str = "microsoft/phi-1.5"  # Default fallback to same if not specified
    tokenizer_path: Optional[str] = None

    # Training Hyperparameters (LoRA/PEFT)
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: str = "q_proj,k_proj,v_proj,o_proj"  # Comma separated

    # Quantization Settings
    use_4bit: bool = True
    bnb_4bit_compute_dtype: str = "float16"
    bnb_4bit_quant_type: str = "nf4"

    # Data Paths
    data_root: str = "data"
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    results_dir: str = "data/results"

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # Hardware Constraints
    max_memory: Optional[str] = None  # e.g., "7GB"
    device_map: str = "auto"

    def __post_init__(self):
        """Initialize tokenizer path if not set."""
        if self.tokenizer_path is None:
            self.tokenizer_path = self.base_model_path

        # Resolve relative paths to absolute if they start with 'data'
        if self.data_root.startswith("data"):
            self.data_root = str(Path(__file__).parent.parent.parent.parent / self.data_root)
        
        # Ensure directories exist (optional, but good for config validation)
        # We do not create them here to avoid side effects during config loading,
        # but we normalize the paths.
    
    def set_seeds(self) -> None:
        """Set random seeds for reproducibility across libraries."""
        random.seed(self.seed)
        np.random.seed(self.numpy_seed)
        try:
            import torch
            torch.manual_seed(self.torch_seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self.torch_seed)
        except ImportError:
            pass

    def get_target_modules_list(self) -> list:
        """Parse comma-separated target modules string into a list."""
        return [m.strip() for m in self.target_modules.split(",") if m.strip()]

# Global config instance
_global_config: Optional[SocraticConfig] = None

def load_config_from_env() -> SocraticConfig:
    """
    Load configuration from environment variables.
    Returns a new SocraticConfig instance.
    """
    config = SocraticConfig(
        seed=int(os.getenv("SCT_SEED", 42)),
        torch_seed=int(os.getenv("SCT_TORCH_SEED", 42)),
        numpy_seed=int(os.getenv("SCT_NUMPY_SEED", 42)),
        python_seed=int(os.getenv("SCT_PYTHON_SEED", 42)),
        
        base_model_path=os.getenv("SCT_BASE_MODEL", "microsoft/phi-1.5"),
        fallback_model_path=os.getenv("SCT_FALLBACK_MODEL", "microsoft/phi-1.5"),
        
        lora_r=int(os.getenv("SCT_LORA_R", 16)),
        lora_alpha=int(os.getenv("SCT_LORA_ALPHA", 32)),
        lora_dropout=float(os.getenv("SCT_LORA_DROPOUT", 0.05)),
        target_modules=os.getenv("SCT_TARGET_MODULES", "q_proj,k_proj,v_proj,o_proj"),
        
        use_4bit=os.getenv("SCT_USE_4BIT", "true").lower() in ("true", "1", "yes"),
        bnb_4bit_compute_dtype=os.getenv("SCT_BNB_4BIT_DTYPE", "float16"),
        bnb_4bit_quant_type=os.getenv("SCT_BNB_4BIT_TYPE", "nf4"),
        
        data_root=os.getenv("SCT_DATA_ROOT", "data"),
        raw_data_dir=os.getenv("SCT_RAW_DATA_DIR", "data/raw"),
        processed_data_dir=os.getenv("SCT_PROCESSED_DATA_DIR", "data/processed"),
        results_dir=os.getenv("SCT_RESULTS_DIR", "data/results"),
        
        log_level=os.getenv("SCT_LOG_LEVEL", "INFO"),
        log_file=os.getenv("SCT_LOG_FILE", None),
        
        max_memory=os.getenv("SCT_MAX_MEMORY", None),
        device_map=os.getenv("SCT_DEVICE_MAP", "auto"),
    )
    return config

def get_config() -> SocraticConfig:
    """
    Get the global configuration instance.
    Loads from environment if not already set.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config_from_env()
    return _global_config

def set_global_config(config: SocraticConfig) -> None:
    """
    Manually set the global configuration instance.
    Useful for testing or overriding environment defaults.
    """
    global _global_config
    _global_config = config