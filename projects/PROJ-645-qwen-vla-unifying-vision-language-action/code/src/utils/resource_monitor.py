import time
import psutil
import os
import logging
from typing import Optional, Callable, Dict, Any
from contextlib import contextmanager

def get_current_ram_gb() -> float:
    """Get current RAM usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def get_elapsed_seconds(start_time: float) -> float:
    """Get elapsed time in seconds since start_time."""
    return time.time() - start_time

def check_ram_limit(limit_gb: float = 7.0) -> bool:
    """
    Check if current RAM usage is within the limit.
    Returns True if within limit, False if exceeded.
    """
    current_ram = get_current_ram_gb()
    if current_ram > limit_gb:
        return False
    return True

def check_wall_time_limit(start_time: float, limit_seconds: float = 21600) -> bool:
    """
    Check if elapsed time is within the wall-time limit.
    Logs a TIMEOUT_WARNING if the limit is exceeded but does not abort.
    Returns True if within limit, False if exceeded.
    """
    elapsed = get_elapsed_seconds(start_time)
    logger = logging.getLogger(__name__)
    
    if elapsed > limit_seconds:
        logger.warning("TIMEOUT_WARNING: Wall-time limit of %s seconds exceeded. Elapsed: %s seconds.", 
                     limit_seconds, elapsed)
        return False
    return True

@contextmanager
def resource_monitor(start_time: float, ram_limit_gb: float = 7.0, 
                    wall_time_limit_seconds: float = 21600):
    """
    Context manager to monitor RAM and wall-time during training.
    Yields elapsed time and current RAM usage.
    """
    try:
        while True:
            elapsed = get_elapsed_seconds(start_time)
            current_ram = get_current_ram_gb()
            
            # Check limits
            ram_ok = check_ram_limit(ram_limit_gb)
            time_ok = check_wall_time_limit(start_time, wall_time_limit_seconds)
            
            if not time_ok:
                # Wall time exceeded, yield but signal stop
                yield {"elapsed": elapsed, "ram_gb": current_ram, "stop": True}
                break
            
            if not ram_ok:
                # RAM exceeded, yield but signal stop
                yield {"elapsed": elapsed, "ram_gb": current_ram, "stop": True}
                break
                
            # Continue monitoring
            yield {"elapsed": elapsed, "ram_gb": current_ram, "stop": False}
            
            # Small sleep to avoid busy waiting
            time.sleep(1)
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Monitoring interrupted by user.")

def auto_reduce_batch_size(current_batch_size: int, min_batch_size: int = 1) -> int:
    """
    Reduce batch size if RAM is too high.
    Returns the new batch size.
    """
    if not check_ram_limit(6.5):  # Check against 6.5GB threshold
        new_size = max(min_batch_size, current_batch_size // 2)
        if new_size != current_batch_size:
            logging.getLogger(__name__).warning(
                "Auto-reducing batch size from %d to %d due to high RAM usage.",
                current_batch_size, new_size
            )
            return new_size
    return current_batch_size

def wait_for_ram_drop(target_gb: float = 6.0, timeout_seconds: float = 300) -> bool:
    """
    Wait for RAM usage to drop below target.
    Returns True if target reached, False if timeout.
    """
    start = time.time()
    while time.time() - start < timeout_seconds:
        if get_current_ram_gb() < target_gb:
            return True
        time.sleep(5)
    return False

def main():
    """Demo of resource monitoring functions."""
    print("Resource Monitor Demo")
    print(f"Current RAM: {get_current_ram_gb():.2f} GB")
    print(f"RAM within 7GB limit: {check_ram_limit(7.0)}")
    print(f"Wall time within 21600s limit: {check_wall_time_limit(time.time(), 21600)}")

if __name__ == "__main__":
    main()
