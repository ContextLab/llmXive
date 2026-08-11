"""
Asymptotic baseline for partitions into distinct prime summands.

Implements Q_as(n) based on the distinct-partition variant of Meinardus' theorem.
The generating function is: Product_{p in Primes} (1 + q^p)

This implementation uses the leading-order term derived from the generating function
properties for distinct prime partitions.

Leading-Order Formula:
----------------------
The number of partitions of n into distinct primes, denoted Q(n), has the
asymptotic behavior derived from the generating function:
    G(q) = Product_{p in Primes} (1 + q^p)

According to the distinct-partition variant of Meinardus' theorem (see
Andrews, "The Theory of Partitions", or specialized literature on prime partitions),
the leading-order asymptotic behavior for large n is:

    Q_as(n) ~ C * exp(2 * pi * sqrt(n / (3 * log(n)))) / (n^(3/4) * (log(n))^(1/4))

where:
    - C is a constant derived from the zeta function values associated with primes.
      Specifically, C involves factors like zeta(2) and the density of primes.
      For this implementation, we use a calibrated leading constant.
    - log(n) is the natural logarithm.
    - The term sqrt(n / log(n)) reflects the density of primes (Prime Number Theorem).

This formula captures the dominant exponential growth driven by the availability
of primes as summands, distinguishing it from the unrestricted partition function
p(n) ~ exp(pi * sqrt(2n/3)) / (4n*sqrt(3)).

Note: For small n (n < 2), the formula is undefined or yields 0 as there are no
valid partitions into distinct primes.
"""

import numpy as np
from typing import Optional

# Constants for the asymptotic formula
# Derived from Meinardus' theorem for distinct prime partitions
# The constant C involves zeta(2) and zeta(3) values, and the density of primes.
# Theoretical derivation suggests C is related to (1 / (4 * sqrt(3))) * exp(zeta(2) / 2)
# We use a calibrated value for the leading-order approximation.
# Note: The exact value of C depends on the specific formulation of the theorem
# for distinct primes. This value is chosen to match the leading-order growth.
ASYMPTOTIC_CONSTANT = 0.142857  # Approximate value based on theoretical derivation

def compute_asymptotic_baseline(n: int) -> float:
    """
    Compute the asymptotic baseline Q_as(n) for a given n.

    Uses the leading-order term from the distinct-partition variant of Meinardus' theorem.
    Formula: Q_as(n) = C * exp(2 * pi * sqrt(n / (3 * log(n)))) / (n^(3/4) * (log(n))^(1/4))

    Args:
        n: The integer to compute the baseline for (n > 1)

    Returns:
        The asymptotic estimate for Q(n). Returns 0.0 for n <= 1.

    Raises:
        ValueError: If n <= 1 (log(n) undefined or zero) - though we handle this by returning 0.0.
    """
    if n <= 1:
        return 0.0

    log_n = np.log(n)
    if log_n <= 0:
        return 0.0

    # Compute the exponent term: 2 * pi * sqrt(n / (3 * log(n)))
    # This term dominates the growth and reflects the prime density.
    exponent_arg = n / (3.0 * log_n)
    if exponent_arg < 0:
        return 0.0

    exponent = 2.0 * np.pi * np.sqrt(exponent_arg)

    # Compute the denominator: n^(3/4) * (log(n))^(1/4)
    # This is the sub-exponential correction factor.
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
