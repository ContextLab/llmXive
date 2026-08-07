"""
Configuration management for the Turbulence Fractal Analysis pipeline.

This module manages Re_λ values, vorticity thresholds, and memory limits.
It provides dataclasses for structured configuration and helper functions
for loading and validating these settings.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import os
import sys
import logging

# Configure logger for this module
_logger = logging.getLogger(__name__)

@dataclass
class TurbulenceConfig:
    """
    Configuration for turbulence simulation parameters.
    
    Attributes:
        re_lambda_values: List of Reynolds numbers (Re_λ) to analyze,
                          representing low to high turbulence intensities.
        vorticity_thresholds: List of multipliers for RMS vorticity to use
                            as iso-surface thresholds (e.g., [2.0, 3.0, 4.0]).
        memory_limit_bytes: Maximum allowed RSS (Resident Set Size) in bytes.
                            Defaults to 6GB.
    """
    re_lambda_values: List[int] = field(default_factory=lambda: [200, 400, 600])
    vorticity_thresholds: List[float] = field(default_factory=lambda: [2.0, 3.0, 4.0])
    memory_limit_bytes: int = 6 * 1024**3  # Default 6 GB
    
    def __post_init__(self):
        if not self.re_lambda_values:
            raise ValueError("re_lambda_values cannot be empty")
        if not self.vorticity_thresholds:
            raise ValueError("vorticity_thresholds cannot be empty")
        if self.memory_limit_bytes <= 0:
            raise ValueError("memory_limit_bytes must be positive")

@dataclass
class PipelineConfig:
    """
    Master configuration container for the entire pipeline.
    
    Attributes:
        turbulence: Turbulence-specific configuration.
        data_path: Root directory for data input/output.
        output_path: Directory for analysis results.
        log_level: Logging verbosity.
    """
    turbulence: TurbulenceConfig = field(default_factory=TurbulenceConfig)
    data_path: str = "data"
    output_path: str = "data/results"
    log_level: str = "INFO"
    
    def __post_init__(self):
        # Ensure paths are absolute or properly formatted relative paths
        if not self.data_path:
            self.data_path = "data"
        if not self.output_path:
            self.output_path = "data/results"

# Global configuration instance
_config: Optional[PipelineConfig] = None

def get_config() -> PipelineConfig:
    """
    Retrieve the current global configuration.
    
    Initializes a default configuration if one does not exist.
    Checks for environment variable overrides for memory limits.
    
    Returns:
        PipelineConfig: The active configuration object.
    """
    global _config
    if _config is None:
        _config = PipelineConfig()
        
        # Allow environment override for memory limit (in GB)
        mem_limit_gb = os.getenv("TURBULENCE_MEMORY_LIMIT_GB")
        if mem_limit_gb:
            try:
                _config.turbulence.memory_limit_bytes = int(float(mem_limit_gb) * 1024**3)
                _logger.info(f"Memory limit overridden by env var: {_config.turbulence.memory_limit_bytes} bytes")
            except ValueError:
                _logger.warning(f"Invalid TURBULENCE_MEMORY_LIMIT_GB value: {mem_limit_gb}, using default.")
        
        # Allow environment override for Re_λ values (comma-separated)
        re_vals = os.getenv("TURBULENCE_RE_LAMBDA")
        if re_vals:
            try:
                _config.turbulence.re_lambda_values = [int(x.strip()) for x in re_vals.split(",")]
                _logger.info(f"Re_λ values overridden by env var: {_config.turbulence.re_lambda_values}")
            except ValueError:
                _logger.warning(f"Invalid TURBULENCE_RE_LAMBDA format, using default.")

        # Allow environment override for thresholds
        thresholds = os.getenv("TURBULENCE_THRESHOLDS")
        if thresholds:
            try:
                _config.turbulence.vorticity_thresholds = [float(x.strip()) for x in thresholds.split(",")]
                _logger.info(f"Vorticity thresholds overridden by env var: {_config.turbulence.vorticity_thresholds}")
            except ValueError:
                _logger.warning(f"Invalid TURBULENCE_THRESHOLDS format, using default.")

    return _config

def validate_config(config: Optional[PipelineConfig] = None) -> bool:
    """
    Validate the current configuration against project constraints.
    
    Checks:
        - Re_λ values are positive integers.
        - Vorticity thresholds are positive floats.
        - Memory limit is within reasonable bounds (e.g., > 1GB).
        - Output path is writable (basic check).
    
    Args:
        config: Optional config to validate. If None, uses get_config().
    
    Returns:
        bool: True if valid, False otherwise.
    
    Raises:
        ValueError: If validation fails with a specific reason.
    """
    cfg = config if config is not None else get_config()
    
    # Validate Re_λ
    if not all(isinstance(r, int) and r > 0 for r in cfg.turbulence.re_lambda_values):
        raise ValueError(f"Re_λ values must be positive integers: {cfg.turbulence.re_lambda_values}")
    
    # Validate thresholds
    if not all(isinstance(t, (int, float)) and t > 0 for t in cfg.turbulence.vorticity_thresholds):
        raise ValueError(f"Vorticity thresholds must be positive numbers: {cfg.turbulence.vorticity_thresholds}")
    
    # Validate memory limit
    min_mem = 1 * 1024**3  # 1 GB minimum
    if cfg.turbulence.memory_limit_bytes < min_mem:
        raise ValueError(f"Memory limit must be at least {min_mem} bytes (1GB).")
    
    # Basic path existence check
    if not os.path.isdir(cfg.data_path):
        _logger.warning(f"Data path '{cfg.data_path}' does not exist. Creating it.")
        os.makedirs(cfg.data_path, exist_ok=True)
    
    if not os.path.isdir(cfg.output_path):
        _logger.warning(f"Output path '{cfg.output_path}' does not exist. Creating it.")
        os.makedirs(cfg.output_path, exist_ok=True)
    
    _logger.info("Configuration validation passed.")
    return True

def reset_config():
    """Reset the global configuration to defaults (useful for testing)."""
    global _config
    _config = None

if __name__ == "__main__":
    # Simple CLI to dump current config for verification
    logging.basicConfig(level=logging.INFO)
    cfg = get_config()
    print(f"Re_λ Values: {cfg.turbulence.re_lambda_values}")
    print(f"Vorticity Thresholds: {cfg.turbulence.vorticity_thresholds}")
    print(f"Memory Limit: {cfg.turbulence.memory_limit_bytes / (1024**3):.2f} GB")
    validate_config(cfg)
    print("Config is valid.")
