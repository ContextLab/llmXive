"""
llmXive Project: Predicting Cognitive Flexibility from Resting-State Functional Connectivity Variability
Code package initialization.

This package contains all modules for the automated science pipeline.
"""

# Expose core configuration utilities at package level for convenience
from code.config import set_seed, get_config

__version__ = "0.1.0"
__author__ = "llmXive Research Team"

__all__ = [
    "set_seed",
    "get_config",
]
