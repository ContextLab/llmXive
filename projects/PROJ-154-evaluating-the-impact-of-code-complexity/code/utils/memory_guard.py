import os
import sys
import time
import logging
from typing import Optional, List, Any, Callable
from dataclasses import dataclass
import yaml
import psutil
import gc

@dataclass
class MemoryConfig:
    """Configuration for memory monitoring thresholds."""
    memory_threshold_percent: float = 85.0
    max_memory_gb: Optional[float] = None
    downsample_factor: float = 0.5
    abort_on_exceed: bool = True

def load_config(config_path: str = "config.yaml") -> MemoryConfig:
    """Load memory configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        if not isinstance(config_data, dict):
            raise ValueError("Config file must contain a dictionary")
        
        return MemoryConfig(
            memory_threshold_percent=config_data.get('memory_threshold_percent', 85.0),
            max_memory_gb=config_data.get('max_memory_gb'),
            downsample_factor=config_data.get('downsample_factor', 0.5),
            abort_on_exceed=config_data.get('abort_on_exceed', True)
        )
    except FileNotFoundError:
        logging.warning(f"Config file {config_path} not found. Using defaults.")
        return MemoryConfig()
    except yaml.YAMLError as e:
        logging.error(f"Error parsing config file: {e}")
        raise

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss / (1024 ** 3)

def check_and_abort_or_downsample(
    current_usage_gb: float,
    config: MemoryConfig,
    batch_data: Optional[List[Any]] = None
) -> tuple[bool, Optional[List[Any]]]:
    """
    Check memory usage and decide whether to abort or downsample.
    
    Returns:
        tuple: (should_abort, downsampled_data)
        - should_abort: True if processing should stop
        - downsampled_data: List with reduced size if downsampled, None otherwise
    """
    # Calculate threshold in GB if max_memory_gb is set
    if config.max_memory_gb is not None:
        threshold_gb = config.max_memory_gb
    else:
        # Use percentage of total system memory
        total_memory_gb = psutil.virtual_memory().total / (1024 ** 3)
        threshold_gb = total_memory_gb * (config.memory_threshold_percent / 100.0)
    
    if current_usage_gb > threshold_gb:
        logging.warning(f"Memory usage {current_usage_gb:.2f}GB exceeds threshold {threshold_gb:.2f}GB")
        
        if not config.abort_on_exceed:
            # Try to downsample
            if batch_data is not None and len(batch_data) > 0:
                new_size = max(1, int(len(batch_data) * config.downsample_factor))
                downsampled_data = batch_data[:new_size]
                logging.info(f"Downsampling batch from {len(batch_data)} to {new_size} items")
                return False, downsampled_data
            else:
                logging.error("Cannot downsample: no batch data provided")
                return True, None
        else:
            logging.error("Memory limit exceeded and abort_on_exceed is True. Aborting.")
            return True, None
    
    return False, None

class MemoryGuard:
    """Context manager for monitoring memory usage during processing."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)
        self.initial_memory_gb = get_memory_usage_gb()
        self.logger = logging.getLogger(__name__)
        self._gc_collected = False
    
    def __enter__(self):
        self.logger.info(f"MemoryGuard initialized. Initial usage: {self.initial_memory_gb:.2f}GB")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        final_memory_gb = get_memory_usage_gb()
        self.logger.info(f"MemoryGuard exiting. Final usage: {final_memory_gb:.2f}GB (Delta: {final_memory_gb - self.initial_memory_gb:.2f}GB)")
        return False  # Don't suppress exceptions
    
    def check_and_handle(self, batch_data: Optional[List[Any]] = None) -> tuple[bool, Optional[List[Any]]]:
        """
        Check current memory usage and handle according to configuration.
        
        Args:
            batch_data: Optional batch of data to potentially downsample
        
        Returns:
            tuple: (should_abort, processed_data)
        """
        current_usage_gb = get_memory_usage_gb()
        should_abort, processed_data = check_and_abort_or_downsample(
            current_usage_gb, self.config, batch_data
        )
        
        if should_abort:
            self.logger.critical("Memory limit exceeded. Aborting execution.")
            # Force garbage collection before aborting
            gc.collect()
            sys.exit(1)
        
        if processed_data is not None:
            self.logger.info(f"Data downsampled to {len(processed_data)} items due to memory pressure")
        
        return should_abort, processed_data
    
    def get_memory_info(self) -> dict:
        """Get current memory information."""
        current_gb = get_memory_usage_gb()
        total_gb = psutil.virtual_memory().total / (1024 ** 3)
        
        return {
            'current_usage_gb': current_gb,
            'total_memory_gb': total_gb,
            'usage_percent': (current_gb / total_gb) * 100,
            'threshold_percent': self.config.memory_threshold_percent,
            'threshold_gb': self.config.max_memory_gb or (total_gb * self.config.memory_threshold_percent / 100)
        }