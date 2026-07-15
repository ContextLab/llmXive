"""
Data generator for simulation.
Implements T007: Base data generator utilities supporting Normal and Multinomial distributions.
"""
import json
import os
from typing import Tuple, Union, Optional, List, Dict
import numpy as np

from code.simulation.logging_config import get_logger, log_operation
from code.simulation import get_rng

logger = get_logger("data_generator")

def validate_distribution_params(dist_type: str, **kwargs) -> bool:
    """Validate distribution parameters."""
    if dist_type == "normal":
        if "mean" not in kwargs or "std" not in kwargs:
            return False
    elif dist_type == "multinomial":
        if "n" not in kwargs or "p" not in kwargs:
            return False
    return True

def generate_normal_data(n: int, mean: float = 0.0, std: float = 1.0, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate normal distribution data.
    """
    rng = get_rng(seed)
    return rng.normal(mean, std, n)

def generate_multinomial_data(n: int, p: List[float], seed: Optional[int] = None) -> np.ndarray:
    """
    Generate multinomial distribution data.
    """
    rng = get_rng(seed)
    return rng.multinomial(n, p)

def generate_contingency_table_data(n: int, p: List[float], shape: Tuple[int, int] = (2, 2), seed: Optional[int] = None) -> np.ndarray:
    """
    Generate contingency table data.
    """
    rng = get_rng(seed)
    counts = rng.multinomial(n, p)
    return counts.reshape(shape)

def generate_two_sample_data(n1: int, n2: int, mean1: float = 0.0, mean2: float = 0.0, std: float = 1.0, seed: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate two sample data for t-test.
    """
    rng = get_rng(seed)
    data1 = rng.normal(mean1, std, n1)
    data2 = rng.normal(mean2, std, n2)
    return data1, data2

def generate_anova_data(n: int, k: int, means: List[float], std: float = 1.0, seed: Optional[int] = None) -> List[np.ndarray]:
    """
    Generate data for ANOVA.
    """
    rng = get_rng(seed)
    groups = []
    for i in range(k):
        group = rng.normal(means[i], std, n)
        groups.append(group)
    return groups

def main():
    """Main entry point for testing."""
    logger.log("data_generator_main")

if __name__ == "__main__":
    main()
