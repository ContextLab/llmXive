"""Monte-Carlo framework core for statistical test validation.

This module provides the core Monte-Carlo simulation functions used to validate
statistical test implementations. It supports z-tests, Fisher's exact tests,
Welch's t-tests, and binomial tests with configurable random seeds for reproducibility.

All functions are designed to be importable and usable by downstream validation
modules (e.g., monte_carlo_validation.py, stat_verification.py).
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
from scipy import stats

# Default random seed from project config (T010)
DEFAULT_SEED: int = 42
DEFAULT_N_REPLICATES: int = 10000


def set_seed(seed: int = DEFAULT_SEED) -> None:
    """Set the random seed for reproducible Monte-Carlo simulations.

    Args:
        seed: Random seed value (default: 42 per T010 config)
    """
    np.random.seed(seed)


def simulate_two_proportion_data(
    n1: int,
    n2: int,
    p1: float,
    p2: float,
    n_replicates: int = 1,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Simulate binary outcome data for two-proportion tests.

    Args:
        n1: Sample size for group 1
        n2: Sample size for group 2
        p1: True proportion for group 1
        p2: True proportion for group 2
        n_replicates: Number of simulation replicates
        seed: Random seed for reproducibility

    Returns:
        Tuple of (x1, n1_arr, x2, n2_arr) where x1, x2 are success counts
        and n1_arr, n2_arr are sample sizes for each replicate.
    """
    if seed is not None:
        np.random.seed(seed)

    x1 = np.random.binomial(n1, p1, n_replicates)
    x2 = np.random.binomial(n2, p2, n_replicates)
    n1_arr = np.full(n_replicates, n1)
    n2_arr = np.full(n_replicates, n2)

    return x1, n1_arr, x2, n2_arr


def simulate_two_sample_continuous_data(
    n1: int,
    n2: int,
    mean1: float,
    mean2: float,
    std1: float,
    std2: float,
    n_replicates: int = 1,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, np.ndarray]:
    """Simulate continuous outcome data for Welch's t-test.

    Args:
        n1: Sample size for group 1
        n2: Sample size for group 2
        mean1: True mean for group 1
        mean2: True mean for group 2
        std1: True standard deviation for group 1
        std2: True standard deviation for group 2
        n_replicates: Number of simulation replicates
        seed: Random seed for reproducibility

    Returns:
        Tuple of (sample1, sample2) arrays for each replicate.
    """
    if seed is not None:
        np.random.seed(seed)

    sample1 = np.random.normal(mean1, std1, (n_replicates, n1))
    sample2 = np.random.normal(mean2, std2, (n_replicates, n2))

    return sample1, sample2


def run_monte_carlo_z_test(
    n1: int,
    n2: int,
    p1: float,
    p2: float,
    n_replicates: int = DEFAULT_N_REPLICATES,
    seed: int = DEFAULT_SEED
) -> Dict[str, Union[float, int, List[float]]]:
    """Run Monte-Carlo simulation for two-proportion z-test.

    Simulates the z-test under the null hypothesis and computes the
    empirical p-value distribution.

    Args:
        n1: Sample size for group 1
        n2: Sample size for group 2
        p1: True proportion for group 1
        p2: True proportion for group 2
        n_replicates: Number of Monte-Carlo replicates (default: 10000)
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing:
            - 'p_values': List of computed p-values
            - 'mean_p': Mean p-value
            - 'std_p': Standard deviation of p-values
            - 'type_1_error_rate': Proportion of p-values < 0.05
            - 'n_replicates': Number of replicates run
    """
    set_seed(seed)

    x1, _, x2, _ = simulate_two_proportion_data(
        n1, n2, p1, p2, n_replicates, seed
    )

    p_values = []
    for i in range(n_replicates):
        # Two-proportion z-test
        p_hat_pooled = (x1[i] + x2[i]) / (n1 + n2)
        se = np.sqrt(p_hat_pooled * (1 - p_hat_pooled) * (1/n1 + 1/n2))
        if se > 0:
            z_stat = (x1[i]/n1 - x2[i]/n2) / se
            p_val = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        else:
            p_val = 1.0
        p_values.append(p_val)

    p_values = np.array(p_values)
    type_1_error_rate = np.mean(p_values < 0.05)

    return {
        'p_values': p_values.tolist(),
        'mean_p': float(np.mean(p_values)),
        'std_p': float(np.std(p_values)),
        'type_1_error_rate': float(type_1_error_rate),
        'n_replicates': n_replicates,
        'alpha': 0.05
    }


def run_monte_carlo_fisher_exact(
    n1: int,
    n2: int,
    p1: float,
    p2: float,
    n_replicates: int = DEFAULT_N_REPLICATES,
    seed: int = DEFAULT_SEED
) -> Dict[str, Union[float, int, List[float]]]:
    """Run Monte-Carlo simulation for Fisher's exact test.

    Simulates 2x2 contingency tables and computes Fisher's exact test p-values.

    Args:
        n1: Sample size for group 1
        n2: Sample size for group 2
        p1: True proportion for group 1
        p2: True proportion for group 2
        n_replicates: Number of Monte-Carlo replicates (default: 10000)
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing:
            - 'p_values': List of computed p-values
            - 'mean_p': Mean p-value
            - 'std_p': Standard deviation of p-values
            - 'type_1_error_rate': Proportion of p-values < 0.05
            - 'n_replicates': Number of replicates run
    """
    set_seed(seed)

    x1, _, x2, _ = simulate_two_proportion_data(
        n1, n2, p1, p2, n_replicates, seed
    )

    p_values = []
    for i in range(n_replicates):
        # Create 2x2 contingency table
        # [[x1, n1-x1], [x2, n2-x2]]
        table = [[x1[i], n1 - x1[i]], [x2[i], n2 - x2[i]]]

        # Fisher's exact test (two-sided)
        try:
            _, p_val = stats.fisher_exact(table, alternative='two-sided')
        except ValueError:
            # Handle edge cases (e.g., all zeros)
            p_val = 1.0
        p_values.append(p_val)

    p_values = np.array(p_values)
    type_1_error_rate = np.mean(p_values < 0.05)

    return {
        'p_values': p_values.tolist(),
        'mean_p': float(np.mean(p_values)),
        'std_p': float(np.std(p_values)),
        'type_1_error_rate': float(type_1_error_rate),
        'n_replicates': n_replicates,
        'alpha': 0.05
    }


def run_monte_carlo_welch_t(
    n1: int,
    n2: int,
    mean1: float,
    mean2: float,
    std1: float,
    std2: float,
    n_replicates: int = DEFAULT_N_REPLICATES,
    seed: int = DEFAULT_SEED
) -> Dict[str, Union[float, int, List[float]]]:
    """Run Monte-Carlo simulation for Welch's t-test.

    Simulates continuous data and computes Welch's t-test p-values.

    Args:
        n1: Sample size for group 1
        n2: Sample size for group 2
        mean1: True mean for group 1
        mean2: True mean for group 2
        std1: True standard deviation for group 1
        std2: True standard deviation for group 2
        n_replicates: Number of Monte-Carlo replicates (default: 10000)
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing:
            - 'p_values': List of computed p-values
            - 'mean_p': Mean p-value
            - 'std_p': Standard deviation of p-values
            - 'type_1_error_rate': Proportion of p-values < 0.05
            - 'n_replicates': Number of replicates run
    """
    set_seed(seed)

    sample1, sample2 = simulate_two_sample_continuous_data(
        n1, n2, mean1, mean2, std1, std2, n_replicates, seed
    )

    p_values = []
    for i in range(n_replicates):
        # Welch's t-test (unequal variances)
        _, p_val = stats.ttest_ind(
            sample1[i], sample2[i], equal_var=False
        )
        p_values.append(p_val)

    p_values = np.array(p_values)
    type_1_error_rate = np.mean(p_values < 0.05)

    return {
        'p_values': p_values.tolist(),
        'mean_p': float(np.mean(p_values)),
        'std_p': float(np.std(p_values)),
        'type_1_error_rate': float(type_1_error_rate),
        'n_replicates': n_replicates,
        'alpha': 0.05
    }


def run_monte_carlo_binomial(
    n: int,
    p: float,
    p_null: float = 0.5,
    n_replicates: int = DEFAULT_N_REPLICATES,
    seed: int = DEFAULT_SEED
) -> Dict[str, Union[float, int, List[float]]]:
    """Run Monte-Carlo simulation for binomial test.

    Simulates binomial outcomes and computes binomial test p-values.

    Args:
        n: Sample size
        p: True probability of success
        p_null: Null hypothesis probability (default: 0.5)
        n_replicates: Number of Monte-Carlo replicates (default: 10000)
        seed: Random seed for reproducibility

    Returns:
        Dictionary containing:
            - 'p_values': List of computed p-values
            - 'mean_p': Mean p-value
            - 'std_p': Standard deviation of p-values
            - 'type_1_error_rate': Proportion of p-values < 0.05
            - 'n_replicates': Number of replicates run
    """
    set_seed(seed)

    successes = np.random.binomial(n, p, n_replicates)

    p_values = []
    for i in range(n_replicates):
        # Two-sided binomial test
        try:
            _, p_val = stats.binomtest(
                successes[i], n, p_null, alternative='two-sided'
            ).pvalue
        except AttributeError:
            # Fallback for older scipy versions
            _, p_val = stats.binom_test(
                successes[i], n, p_null, alternative='two-sided'
            )
        p_values.append(p_val)

    p_values = np.array(p_values)
    type_1_error_rate = np.mean(p_values < 0.05)

    return {
        'p_values': p_values.tolist(),
        'mean_p': float(np.mean(p_values)),
        'std_p': float(np.std(p_values)),
        'type_1_error_rate': float(type_1_error_rate),
        'n_replicates': n_replicates,
        'alpha': 0.05
    }


def validate_monte_carlo_results(
    result: Dict,
    tolerance: float = 0.005
) -> Tuple[bool, str]:
    """Validate Monte-Carlo results against theoretical expectations.

    For null hypothesis simulations (p1=p2 or mean1=mean2), the type_1_error_rate
    should be approximately equal to alpha (0.05) within the specified tolerance.

    Args:
        result: Dictionary from one of the run_monte_carlo_* functions
        tolerance: Acceptable deviation from expected alpha (default: 0.005)

    Returns:
        Tuple of (is_valid, message) where is_valid is True if results pass validation
    """
    alpha = result.get('alpha', 0.05)
    type_1_error_rate = result.get('type_1_error_rate', 0.0)
    n_replicates = result.get('n_replicates', 0)

    # Check if type_1_error_rate is within acceptable range of alpha
    lower_bound = alpha - tolerance
    upper_bound = alpha + tolerance

    if lower_bound <= type_1_error_rate <= upper_bound:
        return True, f"Type I error rate {type_1_error_rate:.4f} within tolerance of alpha={alpha}"
    else:
        return False, f"Type I error rate {type_1_error_rate:.4f} outside tolerance [{lower_bound:.4f}, {upper_bound:.4f}]"


def run_all_monte_carlo_validations(
    test_configs: List[Dict],
    seed: int = DEFAULT_SEED
) -> Dict[str, Dict]:
    """Run multiple Monte-Carlo validations in sequence.

    Args:
        test_configs: List of configuration dictionaries, each containing:
            - 'test_type': One of 'z_test', 'fisher_exact', 'welch_t', 'binomial'
            - 'params': Parameters specific to the test type
        seed: Base random seed (each test gets seed + index)

    Returns:
        Dictionary mapping test_type to result dictionary
    """
    results = {}

    for idx, config in enumerate(test_configs):
        test_type = config['test_type']
        params = config.get('params', {})
        test_seed = seed + idx

        if test_type == 'z_test':
            results['z_test'] = run_monte_carlo_z_test(seed=test_seed, **params)
        elif test_type == 'fisher_exact':
            results['fisher_exact'] = run_monte_carlo_fisher_exact(seed=test_seed, **params)
        elif test_type == 'welch_t':
            results['welch_t'] = run_monte_carlo_welch_t(seed=test_seed, **params)
        elif test_type == 'binomial':
            results['binomial'] = run_monte_carlo_binomial(seed=test_seed, **params)
        else:
            raise ValueError(f"Unknown test_type: {test_type}")

    return results
