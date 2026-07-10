import os
import sys
import time
import logging
from typing import Optional, List, Any, Callable
from dataclasses import dataclass

# Import psutil for memory monitoring
# Note: psutil is listed in requirements.txt (T002)
try:
    import psutil
except ImportError:
    raise ImportError(
        "psutil is required for memory monitoring. "
        "Please install it via 'pip install psutil' or check requirements.txt."
    )

logger = logging.getLogger(__name__)

@dataclass
class MemoryConfig:
    """Configuration for memory monitoring."""
    memory_threshold_percent: float = 85.0
    abort_on_exceed: bool = True
    downsample_factor: float = 0.5
    check_interval_seconds: float = 0.5

def load_config(config_path: str = "config.yaml") -> MemoryConfig:
    """
    Load memory configuration from a YAML file.
    Falls back to defaults if file is missing or key is missing.
    """
    import yaml
    default_config = MemoryConfig()
    
    if not os.path.exists(config_path):
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return default_config

    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return default_config

        threshold = data.get('memory_threshold_percent')
        if threshold is not None:
            default_config.memory_threshold_percent = float(threshold)
        
        abort_flag = data.get('abort_on_exceed')
        if abort_flag is not None:
            default_config.abort_on_exceed = bool(abort_flag)
        
        downsample = data.get('downsample_factor')
        if downsample is not None:
            default_config.downsample_factor = float(downsample)
        
        interval = data.get('check_interval_seconds')
        if interval is not None:
            default_config.check_interval_seconds = float(interval)

        return default_config
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}. Using defaults.")
        return default_config

def get_memory_usage_gb() -> float:
    """
    Get current process memory usage in GB.
    Uses psutil to get RSS (Resident Set Size).
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    # Convert bytes to GB
    return memory_info.rss / (1024 ** 3)

class MemoryGuard:
    """
    Context manager and utility for monitoring memory usage.
    Aborts or downsamples data if usage exceeds the configured threshold.
    """
    def __init__(self, config: Optional[MemoryConfig] = None, config_path: str = "config.yaml"):
        self.config = config or load_config(config_path)
        self.initial_memory: Optional[float] = None
        self.process = psutil.Process(os.getpid())

    def __enter__(self):
        self.initial_memory = get_memory_usage_gb()
        logger.info(f"MemoryGuard initialized. Initial usage: {self.initial_memory:.2f} GB. Threshold: {self.config.memory_threshold_percent}%")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        final_memory = get_memory_usage_gb()
        logger.info(f"MemoryGuard exiting. Final usage: {final_memory:.2f} GB.")
        return False

    def check_and_abort_or_downsample(
        self, 
        current_batch_size: int, 
        data_samples: Optional[List[Any]] = None
    ) -> tuple[bool, Optional[int], Optional[List[Any]]]:
        """
        Checks current memory usage against the threshold.
        
        Args:
            current_batch_size: The size of the current batch being processed.
            data_samples: Optional list of data samples to downsample if needed.
        
        Returns:
            tuple: (should_abort, new_batch_size, downsampled_data)
                - should_abort: True if memory usage is critical and abort is enabled.
                - new_batch_size: Reduced batch size if downsampled, else original.
                - downsampled_data: Downsampled data list if applicable, else original.
        """
        current_usage = get_memory_usage_gb()
        # Calculate threshold in GB based on total system memory
        total_system_memory_gb = psutil.virtual_memory().total / (1024 ** 3)
        threshold_gb = total_system_memory_gb * (self.config.memory_threshold_percent / 100.0)

        if current_usage > threshold_gb:
            logger.warning(
                f"Memory usage ({current_usage:.2f} GB) exceeds threshold ({threshold_gb:.2f} GB). "
                f"Threshold percent: {self.config.memory_threshold_percent}%"
            )

            if self.config.abort_on_exceed:
                logger.error("Memory threshold exceeded and abort is enabled. Terminating process.")
                # Log stack trace for debugging
                logger.error("Stack trace:", exc_info=True)
                sys.exit(1)
            
            # If not aborting, attempt to downsample
            if data_samples is not None and len(data_samples) > 0:
                new_size = max(1, int(len(data_samples) * self.config.downsample_factor))
                # Take the first 'new_size' items (could be random in a real scenario, but deterministic here)
                downsampled = data_samples[:new_size]
                logger.info(f"Downsampling batch from {len(data_samples)} to {new_size} samples.")
                return False, new_size, downsampled
            elif current_batch_size > 1:
                new_size = max(1, int(current_batch_size * self.config.downsample_factor))
                logger.info(f"Downsampling batch size from {current_batch_size} to {new_size}.")
                return False, new_size, None
            else:
                logger.error("Memory critical and batch size is already 1. Cannot downsample further.")
                sys.exit(1)
        
        return False, current_batch_size, data_samples

def check_and_abort_or_downsample(
    config_path: str = "config.yaml",
    current_batch_size: int = 1,
    data_samples: Optional[List[Any]] = None
) -> tuple[bool, int, Optional[List[Any]]]:
    """
    Convenience function to check memory without instantiating a class.
    Loads config from disk, checks usage, and returns action.
    """
    guard = MemoryGuard(config_path=config_path)
    return guard.check_and_abort_or_downsample(current_batch_size, data_samples)