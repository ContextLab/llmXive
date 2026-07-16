"""
Configuration management for the llmXive research pipeline.

This module manages random seeds for reproducibility and runtime limits
(CPU-only enforcement, bounded timeouts) as required by the project constraints.
"""
import os
import random
import sys
import signal
from typing import Optional, Union


class Config:
    """
    Central configuration manager for the research pipeline.
    
    Attributes:
        seed (int): Random seed for reproducibility (default: 42).
        timeout_seconds (Optional[int]): Maximum runtime in seconds (default: None).
        cpu_only (bool): If True, forces CPU-only execution (default: True).
    """
    _instance: Optional['Config'] = None
    
    def __init__(self):
        self._seed: int = 42
        self._timeout_seconds: Optional[int] = None
        self._cpu_only: bool = True
        self._setup_signals()
    
    def _setup_signals(self):
        """Setup signal handlers for timeout enforcement."""
        if self._timeout_seconds is not None:
            # Use SIGALRM on Unix-like systems
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, self._timeout_handler)
                signal.alarm(self._timeout_seconds)
            else:
                # Fallback for Windows: use threading timer
                import threading
                self._timeout_timer = threading.Timer(
                    self._timeout_seconds, 
                    self._timeout_handler_threaded
                )
                self._timeout_timer.daemon = True
                self._timeout_timer.start()
    
    def _timeout_handler(self, signum, frame):
        """Handle timeout signal."""
        raise TimeoutError(f"Execution exceeded the time limit of {self._timeout_seconds} seconds")
    
    def _timeout_handler_threaded(self):
        """Handle timeout for Windows (threaded fallback)."""
        raise TimeoutError(f"Execution exceeded the time limit of {self._timeout_seconds} seconds")
    
    @property
    def seed(self) -> int:
        """Get the current random seed."""
        return self._seed
    
    @seed.setter
    def seed(self, value: int):
        """Set the random seed and propagate to all random number generators."""
        self._seed = value
        random.seed(value)
        if 'numpy' in sys.modules:
            import numpy as np
            np.random.seed(value)
    
    @property
    def timeout_seconds(self) -> Optional[int]:
        """Get the timeout limit in seconds."""
        return self._timeout_seconds
    
    @timeout_seconds.setter
    def timeout_seconds(self, value: Optional[int]):
        """Set the timeout limit and reconfigure signal handlers."""
        self._timeout_seconds = value
        # Re-setup signals with new timeout
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)  # Cancel previous alarm
            if value is not None:
                signal.signal(signal.SIGALRM, self._timeout_handler)
                signal.alarm(value)
    
    @property
    def cpu_only(self) -> bool:
        """Get the CPU-only flag."""
        return self._cpu_only
    
    @cpu_only.setter
    def cpu_only(self, value: bool):
        """Set the CPU-only flag and configure libraries accordingly."""
        self._cpu_only = value
        if value:
            # Force CPU-only for common ML libraries
            if 'torch' in sys.modules:
                import torch
                torch.set_num_threads(1)
            if 'tensorflow' in sys.modules:
                import tensorflow as tf
                tf.config.set_visible_devices([], 'GPU')
            if 'jax' in sys.modules:
                import jax
                jax.config.update('jax_platform_name', 'cpu')
    
    def reset(self):
        """Reset configuration to defaults."""
        self._seed = 42
        self._timeout_seconds = None
        self._cpu_only = True
        random.seed(42)
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)


# Global configuration instance
_config = Config()


def get_seed() -> int:
    """
    Get the current random seed.
    
    Returns:
        int: The current random seed value.
    """
    return _config.seed


def set_seed(seed: int):
    """
    Set the random seed for reproducibility.
    
    Args:
        seed (int): The seed value to use.
    """
    _config.seed = seed


def get_timeout_seconds() -> Optional[int]:
    """
    Get the current timeout limit.
    
    Returns:
        Optional[int]: The timeout in seconds, or None if no limit is set.
    """
    return _config.timeout_seconds


def is_cpu_only() -> bool:
    """
    Check if CPU-only mode is enabled.
    
    Returns:
        bool: True if CPU-only mode is active.
    """
    return _config.cpu_only


def enforce_cpu_only():
    """
    Enforce CPU-only execution by setting the flag and configuring libraries.
    """
    _config.cpu_only = True


def reset_config():
    """Reset all configuration values to defaults."""
    _config.reset()


def configure_from_env():
    """
    Configure the pipeline from environment variables.
    
    Environment variables:
        RESEARCH_SEED: Random seed (default: 42)
        RESEARCH_TIMEOUT: Timeout in seconds (default: None)
        RESEARCH_CPU_ONLY: 'true'/'false' (default: 'true')
    """
    seed_str = os.environ.get('RESEARCH_SEED', '42')
    timeout_str = os.environ.get('RESEARCH_TIMEOUT', None)
    cpu_only_str = os.environ.get('RESEARCH_CPU_ONLY', 'true')
    
    try:
        _config.seed = int(seed_str)
    except ValueError:
        _config.seed = 42
    
    if timeout_str:
        try:
            _config.timeout_seconds = int(timeout_str)
        except ValueError:
            _config.timeout_seconds = None
    
    _config.cpu_only = cpu_only_str.lower() in ('true', '1', 'yes')


if __name__ == '__main__':
    # Demonstrate configuration functionality
    print("Initial configuration:")
    print(f"  Seed: {get_seed()}")
    print(f"  Timeout: {get_timeout_seconds()}")
    print(f"  CPU-only: {is_cpu_only()}")
    
    # Test seed setting
    set_seed(123)
    print(f"\nAfter set_seed(123):")
    print(f"  Seed: {get_seed()}")
    print(f"  Random value: {random.random()}")
    
    # Reset
    reset_config()
    print(f"\nAfter reset:")
    print(f"  Seed: {get_seed()}")
    
    # Test environment configuration
    os.environ['RESEARCH_SEED'] = '999'
    os.environ['RESEARCH_TIMEOUT'] = '60'
    os.environ['RESEARCH_CPU_ONLY'] = 'true'
    configure_from_env()
    print(f"\nAfter configure_from_env:")
    print(f"  Seed: {get_seed()}")
    print(f"  Timeout: {get_timeout_seconds()}")
    print(f"  CPU-only: {is_cpu_only()}")
