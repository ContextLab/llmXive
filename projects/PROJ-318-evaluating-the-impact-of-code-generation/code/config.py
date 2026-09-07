"""
Global configuration and reproducibility settings for the llmXive pipeline.
"""
import os
import logging
import random
import numpy as np
from typing import Optional, Dict, Any
import torch

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SEED = 42
DEFAULT_MAX_MEMORY_MB = 7000  # 7 GB RAM limit
DEFAULT_QUANTIZATION_BITS = 4

class ConfigException(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """
    Container for configuration values.
    This class is instantiated by get_config() to provide a single source of truth.
    """
    def __init__(
        self,
        seed: int = SEED,
        max_memory_mb: int = DEFAULT_MAX_MEMORY_MB,
        quantization_bits: int = DEFAULT_QUANTIZATION_BITS,
        log_level: str = "INFO",
        log_file: Optional[str] = None
    ):
        self.seed = seed
        self.max_memory_mb = max_memory_mb
        self.quantization_bits = quantization_bits
        self.log_level = log_level
        self.log_file = log_file

        # Apply global seed immediately upon instantiation if seed is set
        if self.seed is not None:
            set_global_seed(self.seed)

    def __repr__(self) -> str:
        return (
            f"Config(seed={self.seed}, max_memory_mb={self.max_memory_mb}, "
            f"quantization_bits={self.quantization_bits}, log_level='{self.log_level}')"
        )

# Global configuration instance (lazy initialization)
_global_config: Optional[Config] = None

def get_config() -> Config:
    """
    Returns the global configuration instance.
    If not initialized, creates one with defaults.
    """
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def set_global_seed(seed: int) -> None:
    """
    Sets the random seed for reproducibility across numpy, random, torch, and transformers.
    
    Args:
        seed (int): The seed value to use.
    """
    if seed is None:
        return

    # Set seed for Python's random module
    random.seed(seed)
    
    # Set seed for NumPy
    np.random.seed(seed)
    
    # Set seed for PyTorch (CPU and CUDA)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    
    # Set seed for transformers (which often uses torch or random internally)
    # This ensures any internal randomization in transformers is also seeded
    os.environ['PYTHONHASHSEED'] = str(seed)

def configure_logging(log_level: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configures the root logger for the application.
    
    Args:
        log_level (str, optional): Logging level (e.g., 'DEBUG', 'INFO'). Defaults to config value.
        log_file (str, optional): Path to log file. If None, logs to stdout only.
    
    Returns:
        logging.Logger: The configured root logger.
    """
    config = get_config()
    level_str = log_level or config.log_level
    level = getattr(logging, level_str.upper(), logging.INFO)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file or config.log_file:
        file_path = log_file or config.log_file
        if file_path:
            # Ensure directory exists
            log_dir = os.path.dirname(file_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(file_path)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
    
    return root_logger

def get_device_and_dtype() -> tuple:
    """
    Determines the best available device and data type for model execution.
    
    Returns:
        tuple: (device_str, dtype)
    """
    if torch.cuda.is_available():
        device = "cuda"
        # Prefer float16 on CUDA for performance, unless specific config says otherwise
        dtype = torch.float16
    elif torch.backends.mps.is_available():
        device = "mps"
        dtype = torch.float32  # MPS often has limited float16 support
    else:
        device = "cpu"
        dtype = torch.float32
    
    return device, dtype

def get_quantization_config() -> Optional[Any]:
    """
    Returns the BitsAndBytes quantization configuration if enabled.
    
    Returns:
        Optional[BitsAndBytesConfig]: The quantization config, or None if disabled.
    """
    config = get_config()
    if config.quantization_bits == 4:
        try:
            from transformers import BitsAndBytesConfig
            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16
            )
        except ImportError:
            logging.warning("BitsAndBytesConfig not found. Falling back to no quantization.")
            return None
    elif config.quantization_bits == 8:
        try:
            from transformers import BitsAndBytesConfig
            return BitsAndBytesConfig(
                load_in_8bit=True
            )
        except ImportError:
            logging.warning("BitsAndBytesConfig not found. Falling back to no quantization.")
            return None
    
    return None

def get_rate_limit_config() -> Dict[str, Any]:
    """
    Returns rate limiting configuration for API calls.
    
    Returns:
        Dict[str, Any]: Rate limit settings.
    """
    return {
        "max_retries": 3,
        "retry_delay_seconds": 5,
        "max_requests_per_minute": 60
    }

def get_max_memory_mb() -> int:
    """
    Returns the maximum allowed memory in MB.
    
    Returns:
        int: Max memory in MB.
    """
    return get_config().max_memory_mb

# Initialize logging on module import if environment variable is set
if os.environ.get("LLMXIVE_INIT_LOGGING"):
    configure_logging()