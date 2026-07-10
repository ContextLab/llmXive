"""
Prime Sieve Module for PROJ-799

Implements a memory-optimized Sieve of Eratosthenes to generate all prime numbers
up to a specified limit (default 50,000) for use in partition calculations.
"""

from typing import List, Optional
import numpy as np


def generate_primes(limit: int = 50000) -> List[int]:
    """
    Generate all prime numbers up to `limit` using the Sieve of Eratosthenes.

    This implementation uses a boolean numpy array for memory efficiency,
    which is critical when processing large limits in the context of
    integer partition calculations.

    Parameters
    ----------
    limit : int
        The upper bound (inclusive) for prime generation. Default is 50,000.

    Returns
    -------
    List[int]
        A list of prime numbers in ascending order.

    Raises
    ------
    ValueError
        If limit is less than 2.
    """
    if limit < 2:
        return []

    # Initialize boolean array: True means "potentially prime"
    # Index i corresponds to number i
    # We only need to track up to `limit`
    is_prime = np.ones(limit + 1, dtype=bool)
    is_prime[0] = False
    is_prime[1] = False

    # Sieve of Eratosthenes
    # Only need to sieve up to sqrt(limit)
    sqrt_limit = int(limit**0.5) + 1
    for i in range(2, sqrt_limit):
        if is_prime[i]:
            # Mark multiples of i starting from i*i
            # Using numpy slicing for efficiency
            is_prime[i*i : limit+1 : i] = False

    # Extract primes as a list
    primes = np.nonzero(is_prime)[0].tolist()
    return primes


def get_prime_sieve(limit: int = 50000) -> np.ndarray:
    """
    Return a boolean sieve array where index i is True if i is prime.

    This is useful for O(1) primality checks after initial sieve generation.

    Parameters
    ----------
    limit : int
        The upper bound for the sieve.

    Returns
    -------
    np.ndarray
        Boolean array of shape (limit + 1,) where True indicates a prime number.
    """
    if limit < 2:
        return np.zeros(1, dtype=bool)

    is_prime = np.ones(limit + 1, dtype=bool)
    is_prime[0] = False
    is_prime[1] = False

    sqrt_limit = int(limit**0.5) + 1
    for i in range(2, sqrt_limit):
        if is_prime[i]:
            is_prime[i*i : limit+1 : i] = False

    return is_prime


if __name__ == "__main__":
    # Example usage and simple validation
    primes = generate_primes(100)
    print(f"Primes up to 100: {primes}")
    print(f"Count: {len(primes)}")

    # Verify first few primes
    expected_first_10 = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    assert primes[:10] == expected_first_10, "First 10 primes do not match expected"
    print("Validation passed.")
