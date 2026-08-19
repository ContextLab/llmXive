"""
Data Package - Contains benchmark data generation utilities.
"""
from .benchmarks import (
    generate_training_data,
    generate_test_data,
    verify_independence,
)

__all__ = [
    "generate_training_data",
    "generate_test_data",
    "verify_independence",
]
