from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar
from config import get_data_seed, get_bootstrap_seed, get_shuffle_seed

def calculate_coverage(cis: List[Tuple[float, float]], true_mean: float) -> float:
    """
    Calculate empirical coverage probability.
    Input: List of CIs (tuples of lower, upper).
    Logic: Count how many CIs contain the true_mean, divide by total.
    """
    if not cis:
        return 0.0
    count = sum(1 for ci in cis if ci[0] <= true_mean <= ci[1])
    return count / len(cis)

def calculate_ci_width_stability(cis: List[Tuple[float, float]]) -> float:
    """Calculate the standard deviation of CI widths."""
    if not cis:
        return 0.0
    widths = [ci[1] - ci[0] for ci in cis]
    return np.std(widths)

def calculate_bias_block_bootstrap(data: np.ndarray, block_size: int, n_resamples: int, seed: int) -> List[float]:
    """Placeholder for block bootstrap logic if needed."""
    # Not implemented as per current scope (standard bootstrap used)
    raise NotImplementedError("Block bootstrap not implemented in this scope.")

def mcnemar_test_logic(table: List[List[int]]) -> float:
    """
    Perform McNemar's test on a 2x2 contingency table.
    Input: table = [[a, b], [c, d]] where:
       a = both covered
       b = ordered covered, shuffled not
       c = ordered not, shuffled covered
       d = neither covered
    Returns: p-value.
    """
    try:
        # statsmodels mcnemar expects a 2x2 table
        # result = mcnemar(table, exact=False) -> returns Result instance with pvalue
        result = mcnemar(table, exact=False)
        return result.pvalue
    except Exception as e:
        # If the table is degenerate (e.g., b+c=0), return NaN or 1.0 depending on context
        # Here we return NaN to indicate failure to compute
        return float('nan')

def calculate_coverage_drop_magnitude(ordered_cov: float, shuffled_cov: float) -> float:
    """Calculate the magnitude of coverage drop (ordered vs shuffled)."""
    return abs(ordered_cov - shuffled_cov)

def stratify_by_phi(results: List[Dict[str, Any]]) -> Dict[float, List[Dict[str, Any]]]:
    """Group results by phi value."""
    stratified = {}
    for r in results:
        phi = r['phi']
        if phi not in stratified:
            stratified[phi] = []
        stratified[phi].append(r)
    return stratified
