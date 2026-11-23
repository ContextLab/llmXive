"""
Configuration parameters for the simulation pipeline.
"""
from typing import List, Dict, Any, Literal
from dataclasses import dataclass, field
import numpy as np

@dataclass
class SimulationConfig:
    """Configuration for a single simulation scenario."""
    sample_size: int
    distribution: Literal["normal", "uniform", "log_normal"]
    test_type: Literal["t_test", "anova", "chi_squared"]
    effect_size: float
    alpha: float = 0.05
    n_replicates: int = 1000
    seed: int = 42

# Global constants
MAX_REPLICATES = 10000
LOG_EPSILON = 1e-15
MIN_REPLICATES = 1000
CI_WIDTH_TARGET = 0.01

# CSV Schema Definition for raw_pvalues.csv
RAW_PVALUES_SCHEMA = [
    "sample_size",
    "distribution",
    "test_type",
    "effect_size",
    "replicate_id",
    "p_value"
]

# CSV Schema Definition for validation_report.csv
VALIDATION_REPORT_SCHEMA = [
    "sample_size",
    "distribution",
    "test_type",
    "observed_error_rate",
    "theoretical_alpha",
    "difference",
    "status"
]

def get_simulation_grid() -> List[Dict[str, Any]]:
    """
    Generate the full grid of simulation scenarios.
    
    Returns:
        List of configuration dictionaries.
    """
    sample_sizes = [10, 20, 50, 100, 200, 500, 1000]
    distributions = ["normal", "uniform", "log_normal"]
    test_types = ["t_test", "anova", "chi_squared"]
    effect_sizes = [0.0, 0.5]
    
    grid = []
    seed_base = 42
    
    for n in sample_sizes:
        for dist in distributions:
            for test in test_types:
                for eff in effect_sizes:
                    # Adjust test types for distribution compatibility if needed
                    # For this study, we focus on t-test and anova for continuous,
                    # chi-sq for categorical (simulated via binning if needed, 
                    # but here we assume continuous for t/ANOVA and generated counts for chi2)
                    
                    # Simplified grid for continuous tests (t-test, anova)
                    if test in ["t_test", "anova"]:
                        if dist == "log_normal":
                            # Log-normal is skewed, t-test assumptions might be violated,
                            # but we test sensitivity to this.
                            pass
                        
                        grid.append({
                            "sample_size": n,
                            "distribution": dist,
                            "test_type": test,
                            "effect_size": eff,
                            "alpha": 0.05,
                            "n_replicates": MIN_REPLICATES,
                            "seed": seed_base
                        })
                        seed_base += 1
                    
                    # Chi-squared logic would typically require count data generation
                    # For this specific task, we focus on the t-test/ANOVA sensitivity
                    # as per the primary data generator outputs.
                    # If chi-squared is strictly required with these distributions,
                    # a binning step would be needed in data_generator.
                    # Assuming the grid focuses on the continuous tests for now
                    # or that data_generator handles the mapping.
    
    return grid

def get_test_grid() -> Dict[str, Any]:
    """
    Return metadata about the test types supported.
    
    Returns:
        Dictionary mapping test type to metadata.
    """
    return {
        "t_test": {
            "description": "Independent two-sample t-test",
            "min_n": 2,
            "assumptions": ["normality", "equal_variance"]
        },
        "anova": {
            "description": "One-way ANOVA",
            "min_n": 2,
            "assumptions": ["normality", "equal_variance", "independence"]
        },
        "chi_squared": {
            "description": "Chi-squared test of independence",
            "min_n": 5, # Expected cell count
            "assumptions": ["independence", "sufficient_sample_size"]
        }
    }
