"""
llmXive Statistical Analysis of Early Universe CMB Fluctuations and Topological Defects.

This package provides tools for:
- Downloading and validating Planck CMB data
- Applying Galactic masks and buffer zones
- Computing Minkowski Functionals
- Generating Gaussian and Cosmic String simulations
- Performing statistical hypothesis testing
"""

from .config import Config, get_config, update_config, config

__version__ = "0.1.0"
__all__ = ["Config", "get_config", "update_config", "config"]