"""
utils/resource_monitor.py
Resource monitoring utilities for T017.
Logs RAM/Disk usage and enforces limits.
"""
import os
import sys
import psutil
import logging
from pathlib import Path
from datetime import datetime

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
RESOURCE_LOG_FILE = LOG_DIR / "resource_usage.log"

# Limits (from T004/T017 requirements)
MAX_RAM_GB = 7.0
MAX_DISK_GB = 14.0

def get_memory_usage_gb() -> float:
    """Get current process memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def get_disk_usage_gb() -> float:
    """Get current disk usage for the project directory in GB."""
    # Calculate total size of data/ and code/ directories
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
            except FileNotFoundError:
                pass
    return total_size / (1024 ** 3)

def check_resource_limits() -> bool:
    """
    Check if current resource usage is within limits.
    Returns True if OK, False if exceeded.
    """
    ram = get_memory_usage_gb()
    disk = get_disk_usage_gb()
    
    if ram > MAX_RAM_GB:
        logging.error(f"RAM limit exceeded: {ram:.2f}GB > {MAX_RAM_GB}GB")
        return False
    if disk > MAX_DISK_GB:
        logging.error(f"Disk limit exceeded: {disk:.2f}GB > {MAX_DISK_GB}GB")
        return False
    return True

def log_resource_snapshot():
    """Log current resource usage to resource_usage.log."""
    ram = get_memory_usage_gb()
    disk = get_disk_usage_gb()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = f"[{timestamp}] RAM: {ram:.4f}GB, Disk: {disk:.4f}GB\n"
    
    with open(RESOURCE_LOG_FILE, "a") as f:
        f.write(log_entry)
    
    # Also log to logger if configured
    logger = logging.getLogger("resource_monitor")
    logger.info(f"Resource Snapshot - RAM: {ram:.4f}GB, Disk: {disk:.4f}GB")

def enforce_resource_limits():
    """
    Enforce resource limits. If exceeded, raise an exception.
    """
    if not check_resource_limits():
        raise MemoryError("Resource limits exceeded. Aborting execution.")

def setup_resource_logger():
    """Setup a dedicated logger for resource monitoring."""
    logger = logging.getLogger("resource_monitor")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.FileHandler(RESOURCE_LOG_FILE)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

# Initialize logger on import
resource_logger = setup_resource_logger()
