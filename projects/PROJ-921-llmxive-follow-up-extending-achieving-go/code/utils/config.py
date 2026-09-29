"""
Environment configuration management for llmXive.

Handles seeds, token limits, model paths, and other runtime parameters.
Loads from environment variables with sensible defaults.
"""
import os
import random
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path

@dataclass
class Config:
    """Central configuration container for the llmXive pipeline."""
    
    # Randomness control
    seed: int = 42
    numpy_seed: int = field(init=False)
    torch_seed: int = field(init=False)
    
    # Inference parameters
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    repetition_penalty: float = 1.1
    
    # Model paths
    base_model_path: str = "meta-llama/Meta-Llama-3-8B"
    proxy_model_path: str = "allenai/SciLlama-8B-Instruct"
    
    # Dataset paths (relative to project root)
    mmlu_stem_path: str = "code/data/processed/mmlu_stem.jsonl"
    opensci_reason_path: str = "code/data/processed/opensci_reason.jsonl"
    unified_path: str = "code/data/processed/unified.jsonl"
    scored_path: str = "code/data/processed/scored.jsonl"
    gold_standard_path: str = "data/gold_standard.jsonl"
    
    # Directory paths
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    gold_data_dir: str = "data/gold"
    figures_dir: str = "figures"
    reports_dir: str = "code/analysis/reports"
    
    # Runtime limits
    ram_limit_gb: float = 7.0
    timeout_seconds: int = 300
    
    # Scoring thresholds
    confidence_threshold: float = 0.6
    variance_threshold: float = 1.5
    entropy_threshold: float = 2.0
    
    # Distinctness threshold for multi-sample generation
    distinctness_threshold: float = 0.8
    min_distinct_samples: int = 3
    
    def __post_init__(self):
        """Initialize derived seed values."""
        self.numpy_seed = self.seed
        self.torch_seed = self.seed
    
    def apply_seeds(self):
        """Apply random seeds to numpy, torch, and python random."""
        import random
        random.seed(self.seed)
        
        try:
            import numpy as np
            np.random.seed(self.numpy_seed)
        except ImportError:
            pass
        
        try:
            import torch
            torch.manual_seed(self.torch_seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self.torch_seed)
        except ImportError:
            pass
    
    def resolve_path(self, rel_path: str) -> Path:
        """Resolve a relative path to an absolute Path object."""
        return Path(rel_path)

# Global config instance
_config: Optional[Config] = None

def get_config() -> Config:
    """
    Get the global configuration instance.
    Initializes from environment variables if not already set.
    """
    global _config
    if _config is None:
        _config = init_config()
    return _config

def init_config() -> Config:
    """
    Initialize configuration from environment variables.
    Returns a new Config instance with values overridden by env vars.
    """
    # Helper to get int from env
    def get_env_int(key: str, default: int) -> int:
        val = os.getenv(key)
        return int(val) if val is not None else default

    # Helper to get float from env
    def get_env_float(key: str, default: float) -> float:
        val = os.getenv(key)
        return float(val) if val is not None else default

    # Helper to get str from env
    def get_env_str(key: str, default: str) -> str:
        val = os.getenv(key)
        return val if val is not None else default

    config = Config(
        seed=get_env_int("LLMXIVE_SEED", 42),
        max_tokens=get_env_int("LLMXIVE_MAX_TOKENS", 2048),
        temperature=get_env_float("LLMXIVE_TEMPERATURE", 0.7),
        top_p=get_env_float("LLMXIVE_TOP_P", 0.9),
        repetition_penalty=get_env_float("LLMXIVE_REPETITION_PENALTY", 1.1),
        base_model_path=get_env_str("LLMXIVE_BASE_MODEL", "meta-llama/Meta-Llama-3-8B"),
        proxy_model_path=get_env_str("LLMXIVE_PROXY_MODEL", "allenai/SciLlama-8B-Instruct"),
        ram_limit_gb=get_env_float("LLMXIVE_RAM_LIMIT_GB", 7.0),
        timeout_seconds=get_env_int("LLMXIVE_TIMEOUT_SECONDS", 300),
        confidence_threshold=get_env_float("LLMXIVE_CONFIDENCE_THRESHOLD", 0.6),
        variance_threshold=get_env_float("LLMXIVE_VARIANCE_THRESHOLD", 1.5),
        entropy_threshold=get_env_float("LLMXIVE_ENTROPY_THRESHOLD", 2.0),
        distinctness_threshold=get_env_float("LLMXIVE_DISTINCTNESS_THRESHOLD", 0.8),
        min_distinct_samples=get_env_int("LLMXIVE_MIN_DISTINCT_SAMPLES", 3),
    )

    # Override path-based configs
    config.mmlu_stem_path = get_env_str("LLMXIVE_MMLU_STEM_PATH", config.mmlu_stem_path)
    config.opensci_reason_path = get_env_str("LLMXIVE_OPENSCI_PATH", config.opensci_reason_path)
    config.unified_path = get_env_str("LLMXIVE_UNIFIED_PATH", config.unified_path)
    config.scored_path = get_env_str("LLMXIVE_SCORED_PATH", config.scored_path)
    config.gold_standard_path = get_env_str("LLMXIVE_GOLD_PATH", config.gold_standard_path)
    
    config.raw_data_dir = get_env_str("LLMXIVE_RAW_DATA_DIR", config.raw_data_dir)
    config.processed_data_dir = get_env_str("LLMXIVE_PROCESSED_DATA_DIR", config.processed_data_dir)
    config.gold_data_dir = get_env_str("LLMXIVE_GOLD_DATA_DIR", config.gold_data_dir)
    config.figures_dir = get_env_str("LLMXIVE_FIGURES_DIR", config.figures_dir)
    config.reports_dir = get_env_str("LLMXIVE_REPORTS_DIR", config.reports_dir)

    return config

def reset_config():
    """Reset the global config instance (useful for testing)."""
    global _config
    _config = None

# Convenience function to get specific config values
def get_seed() -> int:
    return get_config().seed

def get_max_tokens() -> int:
    return get_config().max_tokens

def get_temperature() -> float:
    return get_config().temperature

def get_proxy_model_path() -> str:
    return get_config().proxy_model_path

def get_ram_limit_gb() -> float:
    return get_config().ram_limit_gb
