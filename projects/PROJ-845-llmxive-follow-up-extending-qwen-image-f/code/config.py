"""
Configuration management for the llmXive project.

Provides a centralized Config dataclass for reproducible experiments,
resource constraints, and runtime parameters.
"""
from dataclasses import dataclass
from typing import Optional
import os
import logging

# Import the logger utility from the existing codebase
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Config:
    """
    Centralized configuration container for the research pipeline.
    
    Attributes:
        seed (int): Random seed for reproducibility. Default: 42.
        max_ram_gb (float): Maximum allowed RAM usage in GB. Default: 7.0.
        max_runtime_hours (float): Maximum allowed runtime in hours. Default: 6.0.
    """
    seed: int = 42
    max_ram_gb: float = 7.0
    max_runtime_hours: float = 6.0

    @classmethod
    def from_env(cls, prefix: str = "LLMXIVE_") -> "Config":
        """
        Create a Config instance by overriding defaults with environment variables.
        
        Args:
            prefix: Environment variable prefix (e.g., 'LLMXIVE_SEED').
            
        Returns:
            Config: A new configuration instance.
        """
        seed = int(os.getenv(f"{prefix}SEED", 42))
        max_ram = float(os.getenv(f"{prefix}MAX_RAM_GB", 7.0))
        max_time = float(os.getenv(f"{prefix}MAX_RUNTIME_HOURS", 6.0))
        
        logger.info(f"Loading config from environment: seed={seed}, max_ram={max_ram}GB, max_time={max_time}h")
        return cls(seed=seed, max_ram_gb=max_ram, max_runtime_hours=max_time)

    def validate(self) -> None:
        """
        Validate configuration constraints.
        
        Raises:
            ValueError: If configuration values are out of expected bounds.
        """
        if self.seed < 0:
            raise ValueError(f"Seed must be non-negative, got {self.seed}")
        if self.max_ram_gb <= 0:
            raise ValueError(f"Max RAM must be positive, got {self.max_ram_gb}GB")
        if self.max_runtime_hours <= 0:
            raise ValueError(f"Max runtime must be positive, got {self.max_runtime_hours}h")
        
        logger.debug("Configuration validation passed.")