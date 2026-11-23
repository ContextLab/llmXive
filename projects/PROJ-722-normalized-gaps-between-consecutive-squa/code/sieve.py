"""
Squarefree number generation using a linear sieve.

Implements an efficient O(N) sieve to identify squarefree integers up to N.
A number is squarefree if it is not divisible by any perfect square > 1.
"""

import time
from typing import List
from code.logging_config import get_logger
from code.utils import MemoryMonitor, check_memory_limit

logger = get_logger(__name__)

def sieve_squarefree(N: int) -> List[int]:
    """
    Generate all squarefree integers up to N using a linear sieve.

    A number is squarefree if it is not divisible by any perfect square > 1.
    This implementation uses a linear sieve approach that runs in O(N) time.

    Args:
        N: Upper bound (inclusive) for generating squarefree numbers.

    Returns:
        A sorted list of all squarefree integers in the range [1, N].

    Raises:
        ValueError: If N < 1.
    """
    if N < 1:
        raise ValueError(f"N must be at least 1, got {N}")

    logger.info(f"Starting squarefree sieve up to N={N}")

    # Track memory usage
    monitor = MemoryMonitor()
    monitor.start()

    # Start timer for execution time logging
    start_time = time.perf_counter()

    # is_squarefree[i] will be True if i is squarefree
    # We use a boolean array where index represents the number
    is_squarefree = [True] * (N + 1)
    is_squarefree[0] = False  # 0 is not considered squarefree in this context

    # Linear sieve components
    primes = []
    # min_prime_factor[i] stores the smallest prime factor of i
    min_prime_factor = [0] * (N + 1)

    for i in range(2, N + 1):
        if min_prime_factor[i] == 0:
            # i is prime
            min_prime_factor[i] = i
            primes.append(i)

        # Mark multiples of i using primes
        for p in primes:
            if p > min_prime_factor[i] or i * p > N:
                break

            min_prime_factor[i * p] = p

            # Check if i * p is divisible by p^2
            # If i is divisible by p, then i * p is divisible by p^2
            if i % p == 0:
                is_squarefree[i * p] = False

        # Check memory periodically
        if i % 1000000 == 0:
            current_rss = monitor.get_current_rss()
            logger.debug(f"Sieve progress: {i}/{N}, current RSS: {current_rss / 1e6:.2f} MB")
            check_memory_limit(current_rss, limit_bytes=2 * 1024 * 1024 * 1024, logger=logger)

    # Collect all squarefree numbers
    result = [i for i in range(1, N + 1) if is_squarefree[i]]

    # Stop timer and memory monitor
    end_time = time.perf_counter()
    execution_time = end_time - start_time
    peak_rss = monitor.stop()

    # Log execution time and memory peak usage
    logger.info(f"Completed squarefree sieve up to N={N}. Found {len(result)} squarefree numbers.")
    logger.info(f"Execution time: {execution_time:.4f} seconds")
    logger.info(f"Peak memory usage: {peak_rss / 1e6:.2f} MB")

    return result


if __name__ == "__main__":
    # Simple test run
    import sys
    test_n = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    print(f"Testing sieve with N={test_n}")
    squarefree_nums = sieve_squarefree(test_n)
    print(f"Found {len(squarefree_nums)} squarefree numbers up to {test_n}")
    print(f"First 20: {squarefree_nums[:20]}")
    print(f"Last 10: {squarefree_nums[-10:]}")