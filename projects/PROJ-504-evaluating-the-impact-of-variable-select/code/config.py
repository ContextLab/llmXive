"""
Configuration loader for the variable selection impact study.

Manages seeds, OpenML dataset IDs, SNR levels, sparsity levels, and output paths.
All paths are relative to the project root.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional

# Determine project root relative to this file's location
# Project structure: projects/PROJ-504-evaluating-the-impact-of-variable-select/
# This file is at: code/config.py
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@dataclass
class Config:
    """
    Base configuration holder for the research pipeline.
    
    Attributes:
        seed: Random seed for reproducibility.
        openml_ids: List of OpenML dataset IDs to download.
        snr_levels: List of Signal-to-Noise Ratio levels to simulate.
        sparsity_levels: List of sparsity levels (proportion of non-zero coefficients) to simulate.
        output_path: Base directory for processed data and results.
        raw_data_path: Directory for raw downloaded data.
        processed_data_path: Directory for processed simulation data.
        results_path: Directory for analysis results and plots.
        max_retries: Maximum retry attempts for data fetching.
    """
    seed: int = 42
    openml_ids: List[int] = field(default_factory=lambda: [150, 159, 160, 161, 162, 163, 164, 165, 166, 167])
    snr_levels: List[float] = field(default_factory=lambda: [0.5, 1.0, 2.0, 5.0])
    sparsity_levels: List[float] = field(default_factory=lambda: [0.1, 0.2, 0.5, 1.0])
    output_path: str = "data/processed"
    raw_data_path: str = "data/raw"
    results_path: str = "results"
    max_retries: int = 3
    
    def __post_init__(self):
        """Validate and normalize paths after initialization."""
        # Ensure paths are absolute relative to project root
        self._resolve_paths()
        
    def _resolve_paths(self):
        """Convert relative paths to absolute paths based on project root."""
        self.output_path = os.path.join(_BASE_DIR, self.output_path)
        self.raw_data_path = os.path.join(_BASE_DIR, self.raw_data_path)
        self.results_path = os.path.join(_BASE_DIR, self.results_path)
        
        # Create directories if they don't exist
        for path in [self.output_path, self.raw_data_path, self.results_path]:
            os.makedirs(path, exist_ok=True)
        
        # Validate specific configuration values
        if not isinstance(self.seed, int) or self.seed < 0:
            raise ValueError(f"Seed must be a non-negative integer, got {self.seed}")
        
        if not self.openml_ids:
            raise ValueError("openml_ids cannot be empty")
        
        if not all(isinstance(x, (int, float)) and x > 0 for x in self.snr_levels):
            raise ValueError("All SNR levels must be positive numbers")
        
        if not all(isinstance(x, (int, float)) and 0 < x <= 1 for x in self.sparsity_levels):
            raise ValueError("All sparsity levels must be between 0 and 1 (exclusive 0, inclusive 1)")

def get_config() -> Config:
    """
    Factory function to create and return a default configuration.
    
    Returns:
        Config: A fully initialized configuration object with validated paths.
    """
    return Config()

def get_config_with_overrides(overrides: dict) -> Config:
    """
    Create a configuration with specific overrides.
    
    Args:
        overrides: Dictionary of configuration values to override.
    
    Returns:
        Config: A configuration object with applied overrides.
    """
    config = get_config()
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown configuration key: {key}")
    
    # Re-validate after overrides
    config._resolve_paths()
    return config

# Convenience access for direct imports
config = get_config()
