"""
Execution configuration and constraints for the llmXive pipeline.

This module defines global constraints for CPU usage, time limits,
memory (RAM) limits, and random seeds to ensure reproducibility.
"""

import os
import multiprocessing
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ExecutionConfig:
    """
    Global execution constraints for the pipeline.

    Attributes:
        cpu_only (bool): If True, restricts execution to CPU (disables GPU).
        time_limit_seconds (Optional[float]): Maximum allowed runtime in seconds.
            If None, no time limit is enforced.
        ram_limit_gb (float): Maximum allowed RAM usage in Gigabytes.
            Datasets exceeding this will be skipped (see T005a).
        random_seed (int): Global random seed for reproducibility.
        num_workers (int): Number of worker processes for parallel tasks.
            Defaults to the number of CPU cores if not specified.
        max_retries (int): Number of retries for transient failures (e.g., network).
        timeout_per_task_seconds (int): Timeout for individual task execution.
    """
    cpu_only: bool = True
    time_limit_seconds: Optional[float] = None  # No limit by default
    ram_limit_gb: float = 7.0  # Aligned with GitHub Actions free-tier constraints
    random_seed: int = 42
    num_workers: int = field(default_factory=lambda: multiprocessing.cpu_count())
    max_retries: int = 3
    timeout_per_task_seconds: int = 300

    def __post_init__(self):
        """Validate and finalize configuration."""
        if self.ram_limit_gb <= 0:
            raise ValueError("ram_limit_gb must be positive")
        if self.random_seed < 0:
            raise ValueError("random_seed must be non-negative")
        if self.num_workers <= 0:
            raise ValueError("num_workers must be positive")

    def set_seed(self):
        """
        Apply the random seed to the global environment.
        Must be called at the start of the main entry point.
        """
        import random
        import numpy as np
        try:
            import torch
            torch.manual_seed(self.random_seed)
            if self.cpu_only and torch.cuda.is_available():
                torch.cuda.device_count = 0  # Force CPU if flag is set
        except ImportError:
            pass  # PyTorch not installed, ignore

        random.seed(self.random_seed)
        np.random.seed(self.random_seed)


# Global instance of the configuration
# This can be overridden by environment variables or CLI arguments in main.py
CONFIG = ExecutionConfig()


def get_config() -> ExecutionConfig:
    """
    Retrieve the global execution configuration.
    """
    return CONFIG


def set_config_override(
    cpu_only: Optional[bool] = None,
    time_limit_seconds: Optional[float] = None,
    ram_limit_gb: Optional[float] = None,
    random_seed: Optional[int] = None,
    num_workers: Optional[int] = None
) -> None:
    """
    Override specific configuration values.
    Useful for CLI argument parsing or environment variable injection.
    """
    if cpu_only is not None:
        CONFIG.cpu_only = cpu_only
    if time_limit_seconds is not None:
        CONFIG.time_limit_seconds = time_limit_seconds
    if ram_limit_gb is not None:
        CONFIG.ram_limit_gb = ram_limit_gb
    if random_seed is not None:
        CONFIG.random_seed = random_seed
    if num_workers is not None:
        CONFIG.num_workers = num_workers


# Environment variable overrides (optional convenience)
if os.getenv("LLMXIVE_CPU_ONLY", "").lower() == "true":
    CONFIG.cpu_only = True
if os.getenv("LLMXIVE_RAM_LIMIT_GB"):
    try:
        CONFIG.ram_limit_gb = float(os.getenv("LLMXIVE_RAM_LIMIT_GB"))
    except ValueError:
        pass
if os.getenv("LLMXIVE_RANDOM_SEED"):
    try:
        CONFIG.random_seed = int(os.getenv("LLMXIVE_RANDOM_SEED"))
    except ValueError:
        pass
if os.getenv("LLMXIVE_NUM_WORKERS"):
    try:
        CONFIG.num_workers = int(os.getenv("LLMXIVE_NUM_WORKERS"))
    except ValueError:
        pass
if os.getenv("LLMXIVE_TIME_LIMIT"):
    try:
        CONFIG.time_limit_seconds = float(os.getenv("LLMXIVE_TIME_LIMIT"))
    except ValueError:
        pass