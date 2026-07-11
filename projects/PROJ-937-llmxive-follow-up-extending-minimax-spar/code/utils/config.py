"""
Configuration management for llmXive pipeline.

Provides:
- Seed pinning for reproducibility
- Threshold configurations for heuristics
- CPU device enforcement
"""
import os
import random
import numpy as np
import torch
from typing import Dict, Any, Optional, Union


# Default configuration values
DEFAULT_SEED = 42
DEFAULT_CPU_THREADS = 4
DEFAULT_MEMORY_LIMIT_GB = 6.5
DEFAULT_CONTEXT_WINDOW = 4096
DEFAULT_BATCH_SIZE = 1

# Heuristic thresholds
DEFAULT_ENTROPY_THRESHOLD = 0.1
DEFAULT_GRADIENT_THRESHOLD = 0.05
DEFAULT_RECENCY_THRESHOLD = 0.01

# Sensitivity analysis thresholds
SENSITIVITY_THRESHOLDS = [0.01, 0.05, 0.1]


class Config:
    """Central configuration class for the llmXive pipeline."""
    
    def __init__(
        self,
        seed: int = DEFAULT_SEED,
        cpu_threads: int = DEFAULT_CPU_THREADS,
        memory_limit_gb: float = DEFAULT_MEMORY_LIMIT_GB,
        context_window: int = DEFAULT_CONTEXT_WINDOW,
        batch_size: int = DEFAULT_BATCH_SIZE,
        entropy_threshold: float = DEFAULT_ENTROPY_THRESHOLD,
        gradient_threshold: float = DEFAULT_GRADIENT_THRESHOLD,
        recency_threshold: float = DEFAULT_RECENCY_THRESHOLD,
        device: str = "cpu",
        data_dir: str = "data",
        results_dir: str = "results",
        checkpoint_dir: str = "checkpoints"
    ):
        """
        Initialize configuration with validated parameters.
        
        Args:
            seed: Random seed for reproducibility
            cpu_threads: Number of CPU threads to use
            memory_limit_gb: Memory limit in GB (safety buffer below 7GB)
            context_window: Maximum context window size
            batch_size: Batch size for processing
            entropy_threshold: Threshold for block entropy selection
            gradient_threshold: Threshold for gradient magnitude selection
            recency_threshold: Threshold for recency bias selection
            device: Device to run on (enforced to "cpu")
            data_dir: Directory for data files
            results_dir: Directory for results
            checkpoint_dir: Directory for model checkpoints
        """
        # Enforce CPU device
        if device.lower() != "cpu":
            raise ValueError(
                f"Device must be 'cpu' for this project. "
                f"Received: {device}"
            )
        
        self.seed = seed
        self.cpu_threads = cpu_threads
        self.memory_limit_gb = memory_limit_gb
        self.context_window = context_window
        self.batch_size = batch_size
        self.entropy_threshold = entropy_threshold
        self.gradient_threshold = gradient_threshold
        self.recency_threshold = recency_threshold
        self.device = device
        self.data_dir = data_dir
        self.results_dir = results_dir
        self.checkpoint_dir = checkpoint_dir
        
        # Validate thresholds
        self._validate_thresholds()
        
        # Initialize random seeds
        self._init_seeds()
        
        # Set CPU threads
        self._set_cpu_threads()
    
    def _validate_thresholds(self) -> None:
        """Validate that all thresholds are in valid ranges."""
        if not 0.0 <= self.entropy_threshold <= 1.0:
            raise ValueError(
                f"Entropy threshold must be between 0.0 and 1.0. "
                f"Received: {self.entropy_threshold}"
            )
        
        if not 0.0 <= self.gradient_threshold <= 1.0:
            raise ValueError(
                f"Gradient threshold must be between 0.0 and 1.0. "
                f"Received: {self.gradient_threshold}"
            )
        
        if not 0.0 <= self.recency_threshold <= 1.0:
            raise ValueError(
                f"Recency threshold must be between 0.0 and 1.0. "
                f"Received: {self.recency_threshold}"
            )
        
        if self.context_window <= 0:
            raise ValueError(
                f"Context window must be positive. "
                f"Received: {self.context_window}"
            )
        
        if self.batch_size <= 0:
            raise ValueError(
                f"Batch size must be positive. "
                f"Received: {self.batch_size}"
            )
        
        if self.memory_limit_gb <= 0:
            raise ValueError(
                f"Memory limit must be positive. "
                f"Received: {self.memory_limit_gb}"
            )
    
    def _init_seeds(self) -> None:
        """Initialize all random seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    
    def _set_cpu_threads(self) -> None:
        """Set the number of CPU threads for PyTorch."""
        torch.set_num_threads(self.cpu_threads)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "seed": self.seed,
            "cpu_threads": self.cpu_threads,
            "memory_limit_gb": self.memory_limit_gb,
            "context_window": self.context_window,
            "batch_size": self.batch_size,
            "entropy_threshold": self.entropy_threshold,
            "gradient_threshold": self.gradient_threshold,
            "recency_threshold": self.recency_threshold,
            "device": self.device,
            "data_dir": self.data_dir,
            "results_dir": self.results_dir,
            "checkpoint_dir": self.checkpoint_dir
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create Config instance from dictionary."""
        return cls(
            seed=config_dict.get("seed", DEFAULT_SEED),
            cpu_threads=config_dict.get("cpu_threads", DEFAULT_CPU_THREADS),
            memory_limit_gb=config_dict.get("memory_limit_gb", DEFAULT_MEMORY_LIMIT_GB),
            context_window=config_dict.get("context_window", DEFAULT_CONTEXT_WINDOW),
            batch_size=config_dict.get("batch_size", DEFAULT_BATCH_SIZE),
            entropy_threshold=config_dict.get("entropy_threshold", DEFAULT_ENTROPY_THRESHOLD),
            gradient_threshold=config_dict.get("gradient_threshold", DEFAULT_GRADIENT_THRESHOLD),
            recency_threshold=config_dict.get("recency_threshold", DEFAULT_RECENCY_THRESHOLD),
            device=config_dict.get("device", "cpu"),
            data_dir=config_dict.get("data_dir", "data"),
            results_dir=config_dict.get("results_dir", "results"),
            checkpoint_dir=config_dict.get("checkpoint_dir", "checkpoints")
        )
    
    def get_thresholds(self) -> Dict[str, float]:
        """Get all heuristic thresholds as a dictionary."""
        return {
            "entropy": self.entropy_threshold,
            "gradient": self.gradient_threshold,
            "recency": self.recency_threshold
        }
    
    def get_sensitivity_thresholds(self) -> Dict[str, list]:
        """Get sensitivity analysis thresholds for each heuristic."""
        return {
            "entropy": SENSITIVITY_THRESHOLDS,
            "gradient": SENSITIVITY_THRESHOLDS,
            "recency": SENSITIVITY_THRESHOLDS
        }


def get_default_config() -> Config:
    """Return a default configuration instance."""
    return Config()


def create_config_with_overrides(overrides: Dict[str, Any]) -> Config:
    """
    Create a configuration with specified overrides.
    
    Args:
        overrides: Dictionary of configuration values to override
        
    Returns:
        Config instance with overrides applied
    """
    default_config = get_default_config()
    default_dict = default_config.to_dict()
    default_dict.update(overrides)
    return Config.from_dict(default_dict)


# Module-level convenience functions
def enforce_cpu():
    """Force all PyTorch operations to use CPU."""
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    torch.set_default_device("cpu") if hasattr(torch, "set_default_device") else None


def set_random_seed(seed: int = DEFAULT_SEED) -> None:
    """Set all random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_heuristic_thresholds() -> Dict[str, float]:
    """Get default heuristic thresholds."""
    return {
        "entropy": DEFAULT_ENTROPY_THRESHOLD,
        "gradient": DEFAULT_GRADIENT_THRESHOLD,
        "recency": DEFAULT_RECENCY_THRESHOLD
    }


def get_sensitivity_range() -> list:
    """Get the default sensitivity analysis threshold range."""
    return SENSITIVITY_THRESHOLDS
