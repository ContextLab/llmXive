"""
Statistical significance testing for isotropy.

Computes global p-values using max C_l distribution from Monte Carlo.
"""
import numpy as np
from typing import List, Dict

def compute_global_pvalue(
    observed_max_cl: float,
    null_distribution: List[float],
    alpha: float = 0.05
) -> Dict[str, float]:
    """
    Compute global empirical p-value.

    Args:
        observed_max_cl: Maximum C_l from observed data
        null_distribution: List of max C_l values from simulations
        alpha: Significance threshold

    Returns:
        Dict with p_value, decision, and counts
    """
    null_array = np.array(null_distribution)
    count_exceed = np.sum(null_array >= observed_max_cl)
    n_sims = len(null_array)

    p_value = count_exceed / n_sims if n_sims > 0 else 1.0

    decision = "reject_isotropy" if p_value <= alpha else "fail_to_reject"

    return {
        "p_value": p_value,
        "decision": decision,
        "n_sims": n_sims,
        "count_exceed": int(count_exceed),
        "threshold": alpha
    }
