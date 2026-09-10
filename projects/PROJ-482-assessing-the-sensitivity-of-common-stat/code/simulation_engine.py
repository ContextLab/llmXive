import numpy as np
from scipy import stats
from typing import Tuple, Dict, Any, List, Optional, Callable
import logging
import os
import csv
from utils.file_lock import file_lock, write_pvalue_batch

class SimulationResult:
    def __init__(self, sample_size: int, distribution_type: str, test_type: str, p_value: float, hypothesis_type: str):
        self.sample_size = sample_size
        self.distribution_type = distribution_type
        self.test_type = test_type
        self.p_value = p_value
        self.hypothesis_type = hypothesis_type

class AdaptiveRunResult:
    def __init__(self, ci_lower: float, ci_upper: float):
        self.ci_lower = ci_lower
        self.ci_upper = ci_upper

def bootstrap_ci(outcomes: List[bool], n_bootstrap: int = 1000, alpha: float = 0.05) -> Tuple[float, float]:
    """Calculates the bootstrap confidence interval for a list of binary outcomes."""
    means = [np.mean(np.random.choice(outcomes, size=len(outcomes), replace=True)) for _ in range(n_bootstrap)]
    lower = np.percentile(means, alpha / 2 * 100)
    upper = np.percentile(means, (1 - alpha / 2) * 100)
    return lower, upper

def execute_t_test(group1: np.ndarray, group2: np.ndarray) -> float:
    """Executes an independent samples t-test."""
    t_statistic, p_value = stats.ttest_ind(group1, group2)
    return p_value

def execute_anova(groups: List[np.ndarray]) -> float:
    """Executes an ANOVA test."""
    f_statistic, p_value = stats.f_oneway(*groups)
    return p_value

def execute_chi_squared(contingency_table: np.ndarray) -> float:
    """Executes a chi-squared test."""
    chi2_statistic, p_value, _, _ = stats.chi2_contingency(contingency_table)
    return p_value

def execute_fisher_exact(table: np.ndarray) -> float:
    """Executes Fisher's exact test."""
    oddsratio, p_value = stats.fisher_exact(table)
    return p_value

def generate_scenario_data(sample_size: int, distribution_type: str, effect_size: float, hypothesis_type: str) -> Tuple[np.ndarray, np.ndarray]:
    """Generates data for a given scenario."""
    if distribution_type == "normal":
        group1 = np.random.normal(0, 1, sample_size)
        group2 = np.random.normal(effect_size, 1, sample_size)
    elif distribution_type == "uniform":
        group1 = np.random.uniform(0, 1, sample_size)
        group2 = np.random.uniform(effect_size, 1 + effect_size, sample_size)
    elif distribution_type == "lognormal":
        group1 = np.random.lognormal(0, 1, sample_size)
        group2 = np.random.lognormal(np.log(1 + effect_size), 1, sample_size)
    else:
        raise ValueError(f"Unsupported distribution type: {distribution_type}")
    return group1, group2

def run_single_test_replicate(sample_size: int, distribution_type: str, test_type: str, hypothesis_type: str, effect_size: float) -> SimulationResult:
    """Runs a single replicate of the simulation."""
    group1, group2 = generate_scenario_data(sample_size, distribution_type, effect_size, hypothesis_type)

    if test_type == "t_test":
        p_value = execute_t_test(group1, group2)
    elif test_type == "anova":
        p_value = execute_anova([group1, group2])
    elif test_type == "chi_squared":
        contingency_table = np.array([[np.sum(group1 < 0.5), np.sum(group1 >= 0.5)],
                                      [np.sum(group2 < 0.5), np.sum(group2 >= 0.5)]])
        p_value = execute_chi_squared(contingency_table)
    elif test_type == "fisher_exact":
        contingency_table = np.array([[np.sum(group1 < 0.5), np.sum(group1 >= 0.5)],
                                      [np.sum(group2 < 0.5), np.sum(group2 >= 0.5)]])
        p_value = execute_fisher_exact(contingency_table)
    else:
        raise ValueError(f"Unsupported test type: {test_type}")

    return SimulationResult(sample_size, distribution_type, test_type, p_value, hypothesis_type)

def save_raw_pvalues(results: List[SimulationResult], filepath: str) -> None:
    """Saves raw p-values to a CSV file with file locking."""
    with file_lock(filepath):
        with open(filepath, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([r.sample_size, r.distribution_type, r.test_type, r.p_value, r.hypothesis_type])

def count_type_i_and_type_ii_errors(p_values: List[float], alpha: float = 0.05) -> Tuple[int, int]:
    """Counts Type I and Type II errors."""
    type_i_errors = sum(p_value < alpha for p_value in p_values)
    type_ii_errors = len(p_values) - type_i_errors
    return type_i_errors, type_ii_errors

def validate_type_i_error_rates(p_values: List[float], alpha: float = 0.05) -> bool:
    """Validates Type I error rates."""
    type_i_errors, _ = count_type_i_and_type_ii_errors(p_values, alpha)
    error_rate = type_i_errors / len(p_values)
    return abs(error_rate - alpha) < 0.01

def run_adaptive_simulation(sample_size: int, distribution_type: str, test_type: str, hypothesis_type: str, effect_size: float, alpha: float = 0.05, max_replicates: int = 10000) -> AdaptiveRunResult:
    """Runs an adaptive Monte Carlo simulation."""
    replicates = 100
    p_values = []
    while True:
        for _ in range(replicates):
            result = run_single_test_replicate(sample_size, distribution_type, test_type, hypothesis_type, effect_size)
            p_values.append(result.p_value)
            save_raw_pvalues([result], "data/processed/raw_pvalues.csv")

        lower, upper = bootstrap_ci(p_values)
        ci_width = upper - lower

        if ci_width <= 0.01 or replicates >= max_replicates:
            break
        replicates += 100

    return AdaptiveRunResult(lower, upper)

def run_full_simulation_batch(sample_sizes: List[int], distributions: List[str], test_types: List[str], hypothesis_types: List[str], effect_size: float, alpha: float = 0.05, max_replicates: int = 10000) -> None:
    """Runs a full batch of simulations."""
    for sample_size in sample_sizes:
        for distribution in distributions:
            for test_type in test_types:
                for hypothesis_type in hypothesis_types:
                    print(f"Running simulation: sample_size={sample_size}, distribution={distribution}, test_type={test_type}, hypothesis_type={hypothesis_type}")
                    run_adaptive_simulation(sample_size, distribution, test_type, hypothesis_type, effect_size, alpha, max_replicates)

def main():
    """Main function to run the simulation."""
    # Example usage (replace with actual configuration)
    sample_sizes = [50, 100, 500]
    distributions = ["normal", "uniform", "lognormal"]
    test_types = ["t_test", "anova", "chi_squared"]
    hypothesis_types = ["null", "alternative"]
    effect_size = 0.5

    run_full_simulation_batch(sample_sizes, distributions, test_types, hypothesis_types, effect_size)
