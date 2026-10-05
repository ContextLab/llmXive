"""
Resource Guard Module for llmXive Project PROJ-189.

Provides execution guards for CPU-only environments, memory limits, and time limits.
Ensures the pipeline adheres to the constraints:
- CPU Only (No GPU)
- RAM <= 7GB
- Runtime <= 6 hours

Raises ResourceLimitExceededError if any constraint is violated.
"""
import os
import sys
import time
import logging
import threading
from datetime import timedelta, datetime
from typing import Optional, Callable, Any
import psutil

# Configure logger for this module
logger = logging.getLogger(__name__)

# Constants
MAX_RAM_GB = 7.0
MAX_RUNTIME_HOURS = 6.0
MAX_RUNTIME_SECONDS = MAX_RUNTIME_HOURS * 3600

class ResourceLimitExceededError(Exception):
    """Raised when a resource limit (RAM, Time, GPU) is exceeded."""
    pass

class GPUForbiddenError(ResourceLimitExceededError):
    """Raised when a GPU is detected in a CPU-only environment."""
    pass

def check_cpu_only() -> None:
    """
    Checks if any GPU is available.
    Raises GPUForbiddenError if a GPU is detected.
    """
    # Check for NVIDIA GPUs via nvidia-smi if available
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '-L'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        if result.returncode == 0 and result.stdout:
            gpu_info = result.stdout.decode('utf-8')
            if 'GPU' in gpu_info:
                logger.warning(f"GPU detected: {gpu_info.strip()}")
                raise GPUForbiddenError(
                    "GPU detected. This pipeline is configured for CPU-only execution. "
                    "Please disable GPU or set environment variable ALLOW_GPU=1 if intentional."
                )
    except FileNotFoundError:
        # nvidia-smi not found, assume no NVIDIA GPU
        pass
    except Exception as e:
        # Log but don't fail on other nvidia-smi errors (e.g., driver issues) unless specific
        logger.debug(f"Could not check NVIDIA GPU status: {e}")

    # Check for other common GPU libraries (optional, but good for safety)
    try:
        # Check if CUDA is available in torch (if installed)
        import torch
        if torch.cuda.is_available():
            raise GPUForbiddenError(
                "PyTorch CUDA is available. This pipeline is configured for CPU-only execution."
            )
    except ImportError:
        pass
    except GPUForbiddenError:
        raise
    except Exception as e:
        logger.debug(f"Could not check PyTorch CUDA status: {e}")

    logger.info("CPU-only check passed.")

class ResourceMonitor:
    """
    Monitors RAM usage and execution time.
    Can be used as a context manager or a standalone monitor.
    """
    def __init__(self, max_ram_gb: float = MAX_RAM_GB, max_runtime_seconds: float = MAX_RUNTIME_SECONDS):
        self.max_ram_gb = max_ram_gb
        self.max_ram_bytes = int(max_ram_gb * 1024 * 1024 * 1024)
        self.max_runtime_seconds = max_runtime_seconds
        self.start_time: Optional[float] = None
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.peak_memory_mb = 0.0
        self.logger = logging.getLogger(__name__)

    def start(self) -> None:
        """Start the monitoring thread and record start time."""
        self.start_time = time.time()
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        self.logger.info(f"Resource monitor started. Limits: RAM <= {self.max_ram_gb}GB, Time <= {self.max_runtime_seconds}s")

    def stop(self) -> None:
        """Stop the monitoring thread."""
        if self.thread:
            self.stop_event.set()
            self.thread.join(timeout=1.0)
            self.logger.info(f"Resource monitor stopped. Peak Memory: {self.peak_memory_mb:.2f} MB")

    def _monitor_loop(self) -> None:
        """Background loop to check memory usage."""
        process = psutil.Process(os.getpid())
        while not self.stop_event.is_set():
            try:
                mem_info = process.memory_info()
                current_mb = mem_info.rss / (1024 * 1024)
                if current_mb > self.peak_memory_mb:
                    self.peak_memory_mb = current_mb
                
                # Check limit
                current_bytes = int(current_mb * 1024 * 1024)
                if current_bytes > self.max_ram_bytes:
                    raise ResourceLimitExceededError(
                        f"Memory limit exceeded: {current_mb:.2f} MB > {self.max_ram_gb * 1024:.2f} MB"
                    )
                
                # Check time
                if self.start_time:
                    elapsed = time.time() - self.start_time
                    if elapsed > self.max_runtime_seconds:
                        raise ResourceLimitExceededError(
                            f"Time limit exceeded: {elapsed:.2f}s > {self.max_runtime_seconds}s"
                        )
            except ResourceLimitExceededError:
                raise
            except Exception as e:
                self.logger.warning(f"Error during memory monitoring: {e}")
            
            # Sleep interval
            self.stop_event.wait(5.0) # Check every 5 seconds

    def check(self) -> None:
        """
        Perform an immediate check of current resources.
        Raises ResourceLimitExceededError if limits are breached.
        """
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        current_mb = mem_info.rss / (1024 * 1024)
        
        if current_mb > (self.max_ram_gb * 1024):
            raise ResourceLimitExceededError(
                f"Memory limit exceeded: {current_mb:.2f} MB > {self.max_ram_gb * 1024:.2f} MB"
            )
        
        if self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed > self.max_runtime_seconds:
                raise ResourceLimitExceededError(
                    f"Time limit exceeded: {elapsed:.2f}s > {self.max_runtime_seconds}s"
                )

def enforce_resource_limits(func: Callable) -> Callable:
    """
    Decorator to enforce resource limits on a function.
    Checks CPU, starts memory/time monitoring, and ensures cleanup.
    """
    def wrapper(*args, **kwargs) -> Any:
        # 1. Check CPU
        check_cpu_only()
        
        # 2. Initialize and start monitor
        monitor = ResourceMonitor()
        monitor.start()
        
        try:
            logger.info(f"Starting function {func.__name__} with resource guards.")
            result = func(*args, **kwargs)
            logger.info(f"Function {func.__name__} completed successfully.")
            return result
        except ResourceLimitExceededError as e:
            logger.error(f"Resource limit exceeded during {func.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            raise
        finally:
            monitor.stop()
    return wrapper

def main() -> None:
    """
    Entry point for running the resource guard as a script or for testing.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Running Resource Guard Main.")
    
    try:
        check_cpu_only()
        logger.info("CPU check passed.")
        
        monitor = ResourceMonitor()
        monitor.start()
        
        # Simulate some work for testing purposes if run directly
        # In real usage, this decorator or manual start/stop wraps the pipeline logic
        logger.info("Simulating 10 seconds of work...")
        time.sleep(10)
        
        monitor.check()
        monitor.stop()
        
        logger.info("Resource guard test passed.")
        
    except (GPUForbiddenError, ResourceLimitExceededError) as e:
        logger.critical(f"Resource guard failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()