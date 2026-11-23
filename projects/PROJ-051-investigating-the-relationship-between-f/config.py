"""
Configuration management for the turbulence analysis pipeline.
Handles Reynolds numbers, vorticity thresholds, and memory limits.
"""
from dataclasses import dataclass, field
from typing import List, Optional
import os


@dataclass
class TurbulenceConfig:
    """Configuration for turbulence analysis parameters."""
    
    # Reynolds numbers (Re_λ) representing low to high turbulence intensities
    re_lambda_values: List[float] = field(default_factory=lambda: [200.0, 400.0, 600.0])
    
    # Vorticity thresholds for iso-surface extraction (multiples of RMS)
    vorticity_thresholds: List[float] = field(default_factory=lambda: [2.0, 3.0, 4.0])
    
    # Memory constraints (maximum RSS in GB)
    max_memory_gb: float = 6.0
    
    # Chunk size for streaming processing (for 512³ grids)
    chunk_size: int = 64
    
    # Kinematic viscosity (ν) - will be overridden by metadata from DNS data
    kinematic_viscosity: Optional[float] = None
    
    # Random seed for reproducibility
    random_seed: int = 42
    
    # Path to data directory
    data_dir: str = "data"
    
    # Path to output directory
    output_dir: str = "data/results"
    
    # JHTDB API key (optional, for authenticated access)
    jhtdb_api_key: Optional[str] = os.getenv("JHTDB_API_KEY")
    
    # Enable fallback to Phase-Shifted DNS when JHTDB is unavailable
    enable_fallback: bool = True


def get_config() -> TurbulenceConfig:
    """
    Load configuration from environment variables or return defaults.
    
    Returns:
        TurbulenceConfig: The active configuration object.
    """
    # Parse Re_λ values from environment if provided
    re_lambda_str = os.getenv("RE_LAMBDA_VALUES")
    re_lambda_values = None
    if re_lambda_str:
        try:
            re_lambda_values = [float(x.strip()) for x in re_lambda_str.split(",")]
        except ValueError:
            pass
    
    # Parse vorticity thresholds from environment if provided
    vorticity_str = os.getenv("VORTICITY_THRESHOLDS")
    vorticity_thresholds = None
    if vorticity_str:
        try:
            vorticity_thresholds = [float(x.strip()) for x in vorticity_str.split(",")]
        except ValueError:
            pass
    
    # Parse max memory from environment if provided
    max_memory_str = os.getenv("MAX_MEMORY_GB")
    max_memory_gb = None
    if max_memory_str:
        try:
            max_memory_gb = float(max_memory_str)
        except ValueError:
            pass
    
    return TurbulenceConfig(
        re_lambda_values=re_lambda_values if re_lambda_values is not None else [200.0, 400.0, 600.0],
        vorticity_thresholds=vorticity_thresholds if vorticity_thresholds is not None else [2.0, 3.0, 4.0],
        max_memory_gb=max_memory_gb if max_memory_gb is not None else 6.0,
        random_seed=int(os.getenv("RANDOM_SEED", 42)),
        data_dir=os.getenv("DATA_DIR", "data"),
        output_dir=os.getenv("OUTPUT_DIR", "data/results"),
        jhtdb_api_key=os.getenv("JHTDB_API_KEY"),
    )


def validate_config(config: TurbulenceConfig) -> bool:
    """
    Validate the configuration parameters.
    
    Args:
        config: The configuration to validate.
        
    Returns:
        bool: True if configuration is valid, False otherwise.
    """
    if not config.re_lambda_values:
        raise ValueError("At least one Re_λ value must be specified")
    
    if any(r <= 0 for r in config.re_lambda_values):
        raise ValueError("All Re_λ values must be positive")
    
    if not config.vorticity_thresholds:
        raise ValueError("At least one vorticity threshold must be specified")
    
    if any(t <= 0 for t in config.vorticity_thresholds):
        raise ValueError("All vorticity thresholds must be positive")
    
    if config.max_memory_gb <= 0:
        raise ValueError("Maximum memory must be positive")
    
    if config.max_memory_gb > 128:
        # Warn but don't fail for very large values
        import warnings
        warnings.warn("Maximum memory is set to a very high value")
    
    return True
