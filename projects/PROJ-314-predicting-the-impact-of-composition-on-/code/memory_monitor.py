import os
import sys
import logging
import gc
from pathlib import Path
from typing import Optional, Dict, Any
import psutil

from config import get_memory_limit, get_int_config
from . import logger

module_logger = logging.getLogger(__name__)

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def check_memory_limit(limit_gb: Optional[float] = None) -> bool:
    """Check if current memory usage exceeds limit."""
    if limit_gb is None:
        limit_gb = get_memory_limit()
    current = get_memory_usage_gb()
    if current > limit_gb:
        raise MemoryError(f"Memory limit exceeded: {current:.2f}GB > {limit_gb}GB")
    return True

def force_garbage_collection():
    """Force garbage collection to free memory."""
    gc.collect()
    module_logger.info("Forced garbage collection")

def validate_dataset_size(df) -> bool:
    """Validate dataset size is within memory limits."""
    size_gb = df.memory_usage(deep=True).sum() / (1024 ** 3)
    limit = get_memory_limit()
    if size_gb > limit * 0.8:
        module_logger.warning(f"Dataset size {size_gb:.2f}GB approaches limit {limit}GB")
        return False
    return True

def log_memory_usage(stage: str):
    """Log current memory usage."""
    usage = get_memory_usage_gb()
    module_logger.info(f"Memory usage at {stage}: {usage:.3f} GB")
    
    # Write to log file
    log_path = Path("logs/memory_monitor.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a') as f:
        f.write(f"{stage}: {usage:.3f} GB\n")

def main():
    """Main entry point for memory monitoring."""
    module_logger.info("Memory monitor initialized")
    log_memory_usage("Initialization")

if __name__ == "__main__":
    main()
