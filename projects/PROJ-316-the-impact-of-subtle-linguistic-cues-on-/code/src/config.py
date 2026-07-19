"""
Configuration management for the llmXive research pipeline.

Provides centralized management for:
- Random seeds (for reproducibility)
- Runtime limits (CPU-only enforcement, bounded timeouts)
"""
import os
import random
import sys
import signal
from typing import Optional, Union


class Config:
    """Central configuration store for the research pipeline."""
    
    _instance: Optional['Config'] = None
    _seed: int = 42
    _timeout_seconds: int = 3600
    _cpu_only: bool = True
    
    def __new__(cls):
        """Singleton pattern to ensure single configuration instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration from environment variables or defaults."""
        # Only initialize once
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        # Load from environment variables if present
        self._seed = int(os.getenv('RESEARCH_SEED', '42'))
        self._timeout_seconds = int(os.getenv('RESEARCH_TIMEOUT', '3600'))
        self._cpu_only = os.getenv('RESEARCH_CPU_ONLY', 'true').lower() in ('true', '1', 'yes')
        
        self._initialized = True
    
    @property
    def seed(self) -> int:
        """Get the current random seed."""
        return self._seed
    
    @property
    def timeout_seconds(self) -> int:
        """Get the timeout in seconds."""
        return self._timeout_seconds
    
    @property
    def cpu_only(self) -> bool:
        """Get the CPU-only flag."""
        return self._cpu_only
    
    def set_seed(self, seed: int) -> None:
        """Set the random seed for reproducibility."""
        self._seed = seed
        random.seed(seed)
        if 'numpy' in sys.modules:
            import numpy as np
            np.random.seed(seed)
    
    def set_timeout(self, seconds: int) -> None:
        """Set the runtime timeout in seconds."""
        self._timeout_seconds = seconds
    
    def set_cpu_only(self, cpu_only: bool) -> None:
        """Set the CPU-only mode flag."""
        self._cpu_only = cpu_only
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._seed = 42
        self._timeout_seconds = 3600
        self._cpu_only = True
        random.seed(42)
        if 'numpy' in sys.modules:
            import numpy as np
            np.random.seed(42)


def get_seed() -> int:
    """Get the current random seed from the singleton config."""
    return Config()._seed


def set_seed(seed: int) -> None:
    """Set the random seed for all random number generators."""
    config = Config()
    config.set_seed(seed)


def get_timeout_seconds() -> int:
    """Get the runtime timeout in seconds."""
    return Config()._timeout_seconds


def is_cpu_only() -> bool:
    """Check if CPU-only mode is enabled."""
    return Config()._cpu_only


def enforce_cpu_only() -> None:
    """
    Enforce CPU-only mode by setting environment variables
    and disabling GPU acceleration libraries.
    """
    if not is_cpu_only():
        return
    
    # Set environment variables for common ML libraries
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    
    # Disable TensorFlow GPU if available
    if 'tensorflow' in sys.modules:
        import tensorflow as tf
        tf.config.set_visible_devices([], 'GPU')
    
    # Disable PyTorch GPU if available
    if 'torch' in sys.modules:
        import torch
        if torch.cuda.is_available():
            torch.cuda.set_device(torch.device('cpu'))


def reset_config() -> None:
    """Reset the global configuration to defaults."""
    Config().reset()


def configure_from_env() -> None:
    """Re-configure the singleton from environment variables."""
    config = Config()
    config._initialized = False
    config.__init__()


# Convenience functions for direct use
def apply_config() -> None:
    """
    Apply configuration settings at pipeline startup.
    This should be called early in main.py or similar entry points.
    """
    config = Config()
    
    # Set random seeds
    set_seed(config.seed)
    
    # Enforce CPU-only if configured
    enforce_cpu_only()
    
    # Set up timeout handler if needed
    if config.timeout_seconds > 0:
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Pipeline execution exceeded {config.timeout_seconds} seconds")
        
        # Only set alarm on Unix systems
        if hasattr(signal, 'alarm'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(config.timeout_seconds)
