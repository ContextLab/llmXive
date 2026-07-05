"""
Configuration management for the Fractal Dimension and Energy Dissipation pipeline.

This module manages:
- Reynolds number (Re_λ) values representing turbulence intensities.
- Vorticity thresholds for iso-surface extraction.
- Memory constraints (max RSS).
"""

from dataclasses import dataclass
from typing import List, Optional
import os

@dataclass
class TurbulenceConfig:
    """Configuration for turbulence simulation parameters."""
    # Reynolds numbers (Re_λ) to analyze: low to high intensities
    re_lambda_values: List[int]
    
    # Vorticity thresholds relative to RMS (e.g., [2.0, 3.0, 4.0] means 2x, 3x, 4x RMS)
    vorticity_thresholds: List[float]
    
    # Memory constraints
    max_rss_bytes: int  # Maximum allowed Resident Set Size in bytes

    # Default values
    DEFAULT_RE_LAMBDA: List[int] = None
    DEFAULT_THRESHOLDS: List[float] = None
    DEFAULT_MAX_RSS_GB: float = 6.0

    def __post_init__(self):
        if self.DEFAULT_RE_LAMBDA is None:
            self.DEFAULT_RE_LAMBDA = [200, 400, 600]
        if self.DEFAULT_THRESHOLDS is None:
            self.DEFAULT_THRESHOLDS = [2.0, 3.0, 4.0]
        
        # Set defaults if lists are empty
        if not self.re_lambda_values:
            self.re_lambda_values = self.DEFAULT_RE_LAMBDA
        if not self.vorticity_thresholds:
            self.vorticity_thresholds = self.DEFAULT_THRESHOLDS
        
        # Convert max RSS to bytes if provided as GB
        if isinstance(self.max_rss_bytes, float) or isinstance(self.max_rss_bytes, int):
            # If it's a reasonable number (likely GB), convert to bytes
            if self.max_rss_bytes < 1e12: 
                self.max_rss_bytes = int(self.max_rss_bytes * 1e9)

# Global configuration instance
# Can be overridden by environment variables or command line args
def get_config() -> TurbulenceConfig:
    """
    Load configuration from environment variables or use defaults.
    
    Environment Variables:
    - RE_LAMBDA_VALUES: Comma-separated list of Reynolds numbers (e.g., "200,400,600")
    - VORTICITY_THRESHOLDS: Comma-separated list of multipliers (e.g., "2.0,3.0,4.0")
    - MAX_RSS_GB: Maximum memory in GB (default 6.0)
    """
    # Parse Re_λ values
    re_str = os.getenv("RE_LAMBDA_VALUES", "200,400,600")
    re_lambda = [int(x.strip()) for x in re_str.split(",")]
    
    # Parse vorticity thresholds
    thresh_str = os.getenv("VORTICITY_THRESHOLDS", "2.0,3.0,4.0")
    thresholds = [float(x.strip()) for x in thresh_str.split(",")]
    
    # Parse max RSS
    max_rss_str = os.getenv("MAX_RSS_GB", "6.0")
    max_rss = float(max_rss_str)
    
    return TurbulenceConfig(
        re_lambda_values=re_lambda,
        vorticity_thresholds=thresholds,
        max_rss_bytes=max_rss
    )

# Export for external use
config = get_config()

# Constants for validation
MIN_RE_LAMBDA = 100
MAX_RE_LAMBDA = 1000
MIN_THRESHOLD = 1.0
MAX_THRESHOLD = 10.0
MIN_MEMORY_GB = 1.0
MAX_MEMORY_GB = 32.0

def validate_config(cfg: TurbulenceConfig) -> bool:
    """Validate configuration parameters."""
    if not all(MIN_RE_LAMBDA <= r <= MAX_RE_LAMBDA for r in cfg.re_lambda_values):
        raise ValueError(f"Re_λ values must be between {MIN_RE_LAMBDA} and {MAX_RE_LAMBDA}")
    
    if not all(MIN_THRESHOLD <= t <= MAX_THRESHOLD for t in cfg.vorticity_thresholds):
        raise ValueError(f"Vorticity thresholds must be between {MIN_THRESHOLD} and {MAX_THRESHOLD}")
    
    if not (MIN_MEMORY_GB * 1e9 <= cfg.max_rss_bytes <= MAX_MEMORY_GB * 1e9):
        raise ValueError(f"Max RSS must be between {MIN_MEMORY_GB} and {MAX_MEMORY_GB} GB")
    
    return True

# Validate on module load (optional, can be disabled in tests)
if os.getenv("SKIP_CONFIG_VALIDATION") != "1":
    validate_config(config)