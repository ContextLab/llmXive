"""
Configuration management module for llmXive pipeline.
Provides PipelineConfig class and utility functions for resource management.
"""

import os
import sys
from dataclasses import dataclass, field
from typing import Optional, Any, Dict
import resource
import logging

logger = logging.getLogger(__name__)

@dataclass
class PipelineConfig:
    """Configuration for the llmXive pipeline."""
    
    # Resource limits
    max_runtime_hours: float = 6.0
    max_memory_gb: float = 7.0
    
    # Data paths
    data_dir: str = "data"
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    results_dir: str = "data/results"
    figures_dir: str = "figures"
    
    # Model settings
    embedding_model: str = "all-MiniLM-L6-v2"
    llm_model: str = "llama-3-8b-instruct"
    
    # Pipeline settings
    redundancy_threshold: float = 0.95
    jaccard_threshold: float = 0.95
    minhash_num_permutations: int = 128
    
    # Experiment settings
    num_seeds: int = 5
    budgets: list = field(default_factory=lambda: [20, 50, 100])
    
    # Logging
    log_level: str = "INFO"
    log_dir: str = "logs"
    
    def __getattr__(self, name: str) -> Any:
        """
        Permissive fallback for unknown attributes.
        Returns a no-op callable for logger-style methods.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

_config_instance: Optional[PipelineConfig] = None

def get_config() -> PipelineConfig:
    """Get or create the global PipelineConfig instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = PipelineConfig()
    return _config_instance

def format_bytes(num_bytes: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"

def check_system_limits(max_memory_gb: Optional[float] = None) -> Dict[str, Any]:
    """
    Check current system resource usage against limits.
    
    Args:
        max_memory_gb: Maximum allowed memory in GB (uses config default if None)
        
    Returns:
        Dictionary with current usage and limit status
    """
    config = get_config()
    max_mem = max_memory_gb or config.max_memory_gb
    
    # Get current memory usage
    usage = resource.getrusage(resource.RUSAGE_SELF)
    current_memory_mb = usage.ru_maxrss / 1024  # Convert KB to MB (Linux)
    current_memory_gb = current_memory_mb / 1024
    
    # Check limits
    memory_ok = current_memory_gb < max_mem
    
    return {
        "current_memory_gb": current_memory_gb,
        "max_memory_gb": max_mem,
        "memory_ok": memory_ok,
        "max_runtime_hours": config.max_runtime_hours
    }

def update_config(**kwargs) -> PipelineConfig:
    """Update configuration with provided values."""
    config = get_config()
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            logger.warning(f"Unknown config key: {key}")
    return config

def main():
    """Main entry point for config module."""
    config = get_config()
    print(f"Pipeline Configuration:")
    print(f"  Max Runtime: {config.max_runtime_hours} hours")
    print(f"  Max Memory: {config.max_memory_gb} GB")
    print(f"  Data Dir: {config.data_dir}")
    print(f"  Embedding Model: {config.embedding_model}")

if __name__ == "__main__":
    main()
