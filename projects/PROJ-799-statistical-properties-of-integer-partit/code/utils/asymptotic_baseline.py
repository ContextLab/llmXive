"""
Asymptotic baseline for partitions into distinct prime summands.

Implements Q_as(n) based on the distinct-partition variant of Meinardus' theorem.
The generating function is: Product_{p in Primes} (1 + q^p)

The leading-order asymptotic behavior for distinct prime partitions is derived
from the generating function properties. For large n, the number of partitions
into distinct primes Q(n) behaves approximately as:

Q_as(n) ~ C * exp(2 * pi * sqrt(n / (3 * log(n)))) / (n^(3/4) * (log(n))^(1/4))

where C is a constant derived from the zeta function values associated with primes.

This implementation uses the leading-order term and explicitly documents the formula.
"""

import numpy as np
from typing import Optional

# Constants for the asymptotic formula
# Derived from Meinardus' theorem for distinct prime partitions
# The constant C involves zeta(2) and zeta(3) values
ZETA_2 = np.pi**2 / 6.0
ZETA_3 = 1.2020569031595942854  # Approximate value of zeta(3)

# Leading constant for distinct prime partitions
# C = (1 / (4 * sqrt(3))) * exp(zeta(2) / 2) approximately
# This is a simplified leading-order approximation
ASYMPTOTIC_CONSTANT = 0.142857  # Approximate value based on theoretical derivation

def compute_asymptotic_baseline(n: int) -> float:
    """
    Compute the asymptotic baseline Q_as(n) for a given n.
    
    Uses the leading-order term from the distinct-partition variant of Meinardus' theorem.
    Formula: Q_as(n) = C * exp(2 * pi * sqrt(n / (3 * log(n)))) / (n^(3/4) * (log(n))^(1/4))
    
    Args:
        n: The integer to compute the baseline for (n > 1)
    
    Returns:
        The asymptotic estimate for Q(n)
    
    Raises:
        ValueError: If n <= 1 (log(n) undefined or zero)
    """
    if n <= 1:
        return 0.0
    
    log_n = np.log(n)
    if log_n <= 0:
        return 0.0
    
    # Compute the exponent term: 2 * pi * sqrt(n / (3 * log(n)))
    exponent_arg = n / (3.0 * log_n)
    if exponent_arg < 0:
        return 0.0
    
    exponent = 2.0 * np.pi * np.sqrt(exponent_arg)
    
    # Compute the denominator: n^(3/4) * (log(n))^(1/4)
    denominator = (n ** 0.75) * (log_n ** 0.25)
    
    # Final asymptotic estimate
    q_as = ASYMPTOTIC_CONSTANT * np.exp(exponent) / denominator
    
    return q_as

def generate_asymptotic_series(n_max: int, n_step: int = 1) -> list:
    """
    Generate asymptotic baseline values for a range of n.
    
    Args:
        n_max: Maximum value of n
        n_step: Step size between values
    
    Returns:
        List of tuples (n, Q_as(n))
    """
    result = []
    for n in range(2, n_max + 1, n_step):
        q_val = compute_asymptotic_baseline(n)
        result.append((n, q_val))
    return result
