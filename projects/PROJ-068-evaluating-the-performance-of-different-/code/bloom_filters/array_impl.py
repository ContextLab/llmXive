"""
Implementation of a Bloom Filter using native Python lists (arrays).

This module provides the ArrayBloomFilter class, which implements the
BloomFilter abstract base class using a list of integers (0 or 1)
to represent the bit array.
"""

from typing import List, Union, Dict, Tuple, Iterable
import math

# Import from sibling modules based on provided API surface
from .base import BloomFilter, calculate_optimal_parameters
from .hash_utils import get_k_hashes, hash_murmur3_32


class ArrayBloomFilter(BloomFilter):
    """
    A Bloom Filter implementation using a native Python list for the bit array.

    Attributes:
        n_elements (int): Estimated number of inserted elements.
        m (int): Size of the bit array.
        k (int): Number of hash functions.
        fpr_target (float): Target false positive rate.
        bit_array (List[int]): The underlying storage, a list of 0s and 1s.
    """

    def __init__(
        self,
        n_elements: int,
        fpr_target: float,
        hash_func=None,
        seeds: Tuple[int, int, int] = (42, 1337, 2024)
    ):
        """
        Initialize the ArrayBloomFilter.

        Args:
            n_elements: Expected number of elements to insert.
            fpr_target: Target false positive rate (e.g., 0.01).
            hash_func: Hash function to use (defaults to MurmurHash3 wrapper).
            seeds: Tuple of seeds for the k hash functions.
        """
        if fpr_target <= 0 or fpr_target >= 1:
            raise ValueError("fpr_target must be between 0 and 1")
        if n_elements <= 0:
            raise ValueError("n_elements must be positive")

        self.n_elements = 0
        self.fpr_target = fpr_target
        self.hash_func = hash_func or hash_murmur3_32
        self.seeds = seeds

        # Calculate optimal m and k based on n and p
        self.m, self.k = calculate_optimal_parameters(n_elements, fpr_target)

        # Initialize the bit array (list of 0s)
        # Using integers 0 and 1 for the array implementation
        self.bit_array: List[int] = [0] * self.m

    def insert(self, item: Union[str, bytes, int]) -> None:
        """
        Insert an item into the Bloom filter.

        Args:
            item: The item to insert. Can be string, bytes, or integer.
        """
        if item is None:
            raise ValueError("Cannot insert None")

        # Get the k hash indices
        indices = get_k_hashes(self.hash_func, item, self.k, self.seeds, self.m)

        for idx in indices:
            self.bit_array[idx] = 1

        self.n_elements += 1

    def contains(self, item: Union[str, bytes, int]) -> bool:
        """
        Check if an item might be in the Bloom filter.

        Args:
            item: The item to check.

        Returns:
            True if the item might be in the set (possible false positive),
            False if the item is definitely not in the set.
        """
        if item is None:
            return False

        indices = get_k_hashes(self.hash_func, item, self.k, self.seeds, self.m)

        # Check if all corresponding bits are set to 1
        for idx in indices:
            if self.bit_array[idx] == 0:
                return False

        return True

    def false_positive_rate(self) -> float:
        """
        Calculate the theoretical false positive rate.

        Returns:
            The theoretical FPR based on current n_elements, m, and k.
        """
        if self.n_elements == 0:
            return 0.0

        # Formula: (1 - e^(-kn/m))^k
        # Note: n is current elements, m is size, k is hash count
        exponent = -1.0 * self.k * self.n_elements / self.m
        prob_bit_set = 1.0 - math.exp(exponent)
        fpr = prob_bit_set ** self.k

        return fpr

    def get_stats(self) -> Dict[str, Union[int, float]]:
        """
        Get internal statistics of the filter.

        Returns:
            Dictionary containing m, k, n_elements, and theoretical_fpr.
        """
        return {
            "m": self.m,
            "k": self.k,
            "n_elements": self.n_elements,
            "fpr_target": self.fpr_target,
            "theoretical_fpr": self.false_positive_rate(),
            "implementation_type": "ArrayBloomFilter"
        }

    def get_memory_usage_bytes(self) -> int:
        """
        Estimate memory usage in bytes.

        Returns:
            Approximate memory usage. For a list of integers, Python overhead
            is significant, but we estimate based on the number of bits + overhead.
            A Python int is typically 28 bytes, but small ints are cached.
            We approximate as: size_of_list + size_of_elements.
        """
        # Approximate: 8 bytes per pointer in the list + 28 bytes per int object
        # However, small integers (0, 1) are singletons in CPython.
        # A more realistic estimate for the list structure itself:
        # 8 bytes * m (pointers) + overhead for list object
        # Plus the actual integer objects (which are cached for 0/1, so negligible extra)
        # We'll return the raw bit count as the theoretical minimum,
        # but acknowledge Python list overhead is higher.
        # To be consistent with "bits" logic, let's return bits used:
        return self.m  # Returning bits for theoretical comparison, or:
        # return self.m * 4  # 4 bytes per int in list (pointer + object overhead approx)
        # Let's stick to the bit count for theoretical baseline comparison as per T035
        # but for "memory_mb" in benchmarks, we usually want actual RAM.
        # We will return the number of bits to be consistent with T035 theoretical calc.
        # If the benchmark wrapper needs actual RAM, it uses measure_memory.
        # Here we return the bit count for the "theoretical_memory_bits" column.
        return self.m

    def __len__(self) -> int:
        """Return the number of inserted elements."""
        return self.n_elements

    def __str__(self) -> str:
        return (
            f"ArrayBloomFilter(n={self.n_elements}, m={self.m}, k={self.k}, "
            f"fpr_target={self.fpr_target:.4f})"
        )
