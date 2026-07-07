"""
Configuration management for the linguistic cues research pipeline.

This module manages random seeds for reproducibility and runtime limits
to ensure CPU-only execution and bounded timeouts as per project constraints.
"""
import os
import random
from typing import Optional, Union

# Default random seed for reproducibility
DEFAULT_SEED = 42

# Default runtime limits (seconds)
DEFAULT_TIMEOUT_SECONDS = 3600  # 1 hour limit

# Flag for CPU-only execution (no GPU acceleration)
CPU_ONLY_DEFAULT = True

# Environment variable names
ENV_SEED = "LLMXIVE_RANDOM_SEED"
ENV_TIMEOUT = "LLMXIVE_TIMEOUT_SECONDS"
ENV_CPU_ONLY = "LLMXIVE_CPU_ONLY"


def get_seed() -> int:
    """
    Retrieve the random seed from environment or use default.
    
    Returns:
        int: The random seed to use for all random number generators.
    """
    seed_str = os.getenv(ENV_SEED)
    if seed_str is not None:
        try:
            return int(seed_str)
        except ValueError:
            raise ValueError(f"Invalid seed value in {ENV_SEED}: {seed_str}")
    return DEFAULT_SEED


def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility across libraries.
    
    Args:
        seed: The seed value. If None, uses the value from environment or default.
    """
    if seed is None:
        seed = get_seed()
    
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    
    # Attempt to set numpy seed if available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    
    # Attempt to set torch seed if available (CPU only)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            # Force CPU-only execution as per constraints
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


def get_timeout_seconds() -> int:
    """
    Retrieve the runtime timeout limit from environment or use default.
    
    Returns:
        int: The maximum allowed runtime in seconds.
    """
    timeout_str = os.getenv(ENV_TIMEOUT)
    if timeout_str is not None:
        try:
            return int(timeout_str)
        except ValueError:
            raise ValueError(f"Invalid timeout value in {ENV_TIMEOUT}: {timeout_str}")
    return DEFAULT_TIMEOUT_SECONDS


def is_cpu_only() -> bool:
    """
    Check if CPU-only execution is enforced.
    
    Returns:
        bool: True if execution should be restricted to CPU.
    """
    cpu_env = os.getenv(ENV_CPU_ONLY)
    if cpu_env is not None:
        return cpu_env.lower() in ("true", "1", "yes", "on")
    return CPU_ONLY_DEFAULT


def enforce_cpu_only() -> None:
    """
    Enforce CPU-only execution by setting environment variables and library configs.
    
    This function should be called early in the pipeline initialization.
    """
    if is_cpu_only():
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ["PYTORCH_NO_CUDA"] = "1"
        
        # Disable GPU for common libraries
        try:
            import torch
            torch.set_num_threads(1)  # Limit threads for CPU-only
        except ImportError:
            pass
        
        try:
            import tensorflow as tf
            tf.config.set_visible_devices([], 'GPU')
        except ImportError:
            pass
        except RuntimeError:
            pass  # TF might not be initialized yet


class Config:
    """
    Configuration container for the research pipeline.
    
    Attributes:
        seed (int): Random seed for reproducibility.
        timeout_seconds (int): Maximum runtime in seconds.
        cpu_only (bool): Whether to enforce CPU-only execution.
    """
    
    def __init__(self, seed: Optional[int] = None, 
                 timeout_seconds: Optional[int] = None,
                 cpu_only: Optional[bool] = None):
        """
        Initialize configuration.
        
        Args:
            seed: Random seed. If None, uses environment or default.
            timeout_seconds: Runtime limit. If None, uses environment or default.
            cpu_only: CPU-only flag. If None, uses environment or default.
        """
        self.seed = get_seed() if seed is None else seed
        self.timeout_seconds = get_timeout_seconds() if timeout_seconds is None else timeout_seconds
        self.cpu_only = is_cpu_only() if cpu_only is None else cpu_only
    
    def __repr__(self) -> str:
        return (f"Config(seed={self.seed}, "
                f"timeout_seconds={self.timeout_seconds}, "
                f"cpu_only={self.cpu_only})")
    
    def apply(self) -> None:
        """
        Apply this configuration to the runtime environment.
        
        This sets random seeds and enforces CPU-only execution.
        """
        set_seed(self.seed)
        if self.cpu_only:
            enforce_cpu_only()