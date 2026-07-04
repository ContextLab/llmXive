"""
Generator module for chaotic time-series data.
"""
from .lorenz import generate_lorenz
from .rossler import generate_rossler

__all__ = ["generate_lorenz", "generate_rossler"]
