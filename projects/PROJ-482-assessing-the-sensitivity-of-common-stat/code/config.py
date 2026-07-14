"""
Configuration module for simulation parameters.

Defines dataclasses and helper functions for simulation grids,
sample sizes, distributions, and statistical test configurations.
"""
from typing import List, Dict, Any, Literal
from dataclasses import dataclass
import numpy as np

# Supported distribution types
DistributionType = Literal["normal", "uniform", "log-normal"]
TestType = Literal["t-test", "anova", "chi-squared", "fisher-exact"]

@dataclass
class SimulationConfig:
    """Configuration for a single simulation run."""
    sample_size: int
    distribution: DistributionType
    test_type: TestType
    effect_size: float = 0.0  # 0.0 for null, >0 for alternative
    alpha: float = 0.05
    n_replicates: int = 1000
    seed: int = 42

def get_simulation_grid() -> List[Dict[str, Any]]:
    """
    Generate the full grid of simulation scenarios.
    
    Returns:
        List of dictionaries, each representing a unique scenario.
    """
    sample_sizes = [10, 20, 50, 100, 200, 500, 1000]
    distributions: List[DistributionType] = ["normal", "uniform", "log-normal"]
    test_types: List[TestType] = ["t-test", "anova", "chi-squared"]
    effect_sizes = [0.0, 0.5]  # Null and Alternative hypotheses

    grid = []
    for n in sample_sizes:
        for dist in distributions:
            for test in test_types:
                for effect in effect_sizes:
                    grid.append({
                        "sample_size": n,
                        "distribution": dist,
                        "test_type": test,
                        "effect_size": effect,
                        "alpha": 0.05,
                        "n_replicates": 1000,
                        "seed": 42
                    })
    return grid

def get_test_grid() -> Dict[str, Any]:
    """
    Return metadata about available statistical tests.
    
    Returns:
        Dictionary mapping test names to their properties.
    """
    return {
        "t-test": {
            "description": "Independent two-sample t-test",
            "min_sample_size": 2,
            "assumptions": ["normality", "homogeneity of variance"]
        },
        "anova": {
            "description": "One-way ANOVA",
            "min_sample_size": 3,
            "assumptions": ["normality", "homogeneity of variance", "independence"]
        },
        "chi-squared": {
            "description": "Chi-squared test of independence",
            "min_sample_size": 4,
            "assumptions": ["expected cell count >= 5 (mostly)"]
        },
        "fisher-exact": {
            "description": "Fisher's Exact test (fallback for small counts)",
            "min_sample_size": 4,
            "assumptions": ["fixed marginals"]
        }
    }
