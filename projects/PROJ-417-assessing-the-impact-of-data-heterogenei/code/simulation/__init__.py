"""
Simulation module for generating synthetic meta-analysis datasets.

Exposes core classes and functions for data generation with controlled
heterogeneity levels.
"""

from .generator import generate_replicates, create_base_dataset

__all__ = [
    "generate_replicates",
    "create_base_dataset",
]
